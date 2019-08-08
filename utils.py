import datetime
import cloudpickle

import numpy as np
import scipy as sp
import pandas as pd
import dask.dataframe as dd

from sklearn.preprocessing import RobustScaler
from sklearn.cluster import KMeans


def append_rul_days_column(drive_data):
    """Appends remaining-useful-life column to pandas/dask dataframe
    RUL is calculated in terms of days. It is the difference between the date
    on which a disk failed (or if it hasnt failed, then max date of observation)
    and the current row (entry in time series) date

    Arguments:
        drive_data {dataframe.groupby.group} -- group of a given hard drive

    Returns:
        dask.dataframe/pandas.DataFrame -- dataframe with the added column
    """
    return drive_data.assign(rul_days=drive_data['date'].max()-drive_data['date'])


def featurize_ts(df, drop_cols=('date', 'failure', 'capacity_bytes', 'rul'), cap=True, num_days=False):
    # group by serials, drop cols which are not to be aggregated
    grouped_df = df.drop(drop_cols, axis=1).groupby('serial_number')

    # vanilla mean values of features across time
    means = grouped_df.mean()
    means = means.rename(columns={col: 'mean_' + col for col in means.columns})

    # vanilla std values of features across time
    stds = grouped_df.std(ddof=0)
    stds = stds.rename(columns={col: 'std_' + col for col in stds.columns})
    stds = stds.fillna(0)    # FIXME: std returns nans even for ddof=0

    # combine features into one df
    feats = means.merge(stds, left_index=True, right_index=True)
    
    # capacity of hard drive
    if cap:
        capacities = df[['serial_number', 'capacity_bytes']].groupby('serial_number').max()
        feats = feats.merge(capacities, left_index=True, right_index=True)
    
    # number of days of observed data available
    if num_days:
        days_per_drive = grouped_df.size().to_frame('num_days')
        feats = feats.merge(days_per_drive, left_index=True, right_index=True)

    return feats


def get_drive_data_from_json(fnames, serial_numbers):
    # get data for only one failed and one working serial number from the last three days
    subdfs = []
    for fname in fnames:
        # read in raw json
        df = pd.read_json(fname, lines=True)
        # convert to df format to index for serial number. then append to list of sub-dfs
        subdfs.append(df[df['smartctl_json'].apply(pd.Series)['serial_number'].isin(serial_numbers)])

    # merge all sub-dfs into one
    return pd.concat(subdfs, ignore_index=True)


def get_downsampled_working_sers(df, num_serials=300, model=None, scaler=None):
    """Downsample the input dataframe of working hard drives by selecting best
    representatives of the data using clustering. Return the identifiers
    (serial numbers) of these best representative hard drives (cluster centers)

    Arguments:
        df {pd.DataFrame} -- dataframe where each row is the feature vector of
                                a given data point (hard drive)

    Keyword Arguments:
        num_serials {int} -- number of hard drives to keep (default: {300})
        model {[type]} -- clustering model to be used for finding best hard
                            drives (default: {None})
        scaler {[type]} -- scaler to scale the raw input data (default: {None})

    Returns:
        list -- serial numbers of cluster centers (best repr hard drives)
    """
    # default to robust scaler
    if scaler is None:
        scaler = RobustScaler()

    # default to vanilla kmeans
    if model is None:
        model = KMeans(n_clusters=num_serials,
                    max_iter=1e6,
                    n_jobs=-1)

    # fit model to scaled data
    model.fit(scaler.fit_transform(df))

    # iterate over centers to find the serials that were closest to each center
    working_best_serials = []
    
    # if model was not dask, dd.compute returns tuple of len 1
    cluster_centers = dd.compute(model.cluster_centers_)
    if isinstance(cluster_centers, tuple):
        cluster_centers = cluster_centers[0]
    
    for i, c in enumerate(cluster_centers):
        # all the points that belong to this cluster
        cluster_pts = dd.compute(df.iloc[model.labels_==i])
        if isinstance(cluster_pts, tuple):
            cluster_pts = cluster_pts[0]

        # distance of each point to the center
        min_dist_idx = np.argmin(sp.spatial.distance.cdist(cluster_pts, c.reshape(1, -1), metric='euclidean'))
        working_best_serials.append(cluster_pts.iloc[min_dist_idx].name)

    return working_best_serials


def get_nan_count_percent(df, divisor=None):
    """Calculates the number of nan values per column,
        both as an absolute amount and as a percentage of some pre-defined "total" amount

    Arguments:
        df {pandas.DataFrame/dask.dataframe} -- dataframe whose nan count to generate

    Keyword Arguments:
        divisor {int/float} -- the "total" amount for calculating percentage.
                                If value in count column is n, value in percent column
                                will be n/divisor.
                                If not provided, number of rows is used by default
                                (default: {None})

    Returns:
        ret_df {pandas.DataFrame/dask.dataframe} -- dataframe with counts and percentages
                                                    of nans in each column of input df.
                                                    Column name is the index, "count" and
                                                    "percent" are the two columns.
    """
    # if total count is not provided, use the number of rows
    if divisor is None:
        # NOTE: len must be used, not shape because in case of dask dataframe
        # shape returns a delayed computation, not an actual value. but
        # len returns an actual value
        divisor = len(df)

    # get count and convert series to dataframe
    ret_df = df.isna().sum().to_frame("count")

    # add percent column
    ret_df["percent"] = ret_df["count"] / divisor

    return ret_df


def get_vendor(model_name):
    """Returns the vendor/manufacturer name for a given hard drive model name

    Arguments:
        model_name {str} -- model name of the hard drive

    Returns:
        str -- vendor name
    """
    if model_name.startswith("W"):
        return "WDC"
    elif model_name.startswith("T"):
        return "Toshiba"
    elif model_name.startswith("S"):
        return "Seagate"
    elif model_name.startswith("Hi"):
        return "Hitachi"
    else:
        return "HGST"


def optimal_repartition_df(df, partition_size_bytes=None):
    # ideal partition size as recommended in dask docs
    if partition_size_bytes is None:
        partition_size_bytes = 100 * 10**6

    # determine number of partitions
    df_size_bytes = df.memory_usage(deep=True).sum().compute()
    num_partitions = int(np.ceil(df_size_bytes / partition_size_bytes))

    # repartition
    return df.repartition(npartitions=num_partitions)


def save_model(model, fname, suffix=None):
    """Serialize and save a dask or sklearn model

    Arguments:
        model {dask_ml or sklearn object} -- trained model to save
        fname {str} -- name of file to write to. saved in the current dir
                        if path-like name is not provided

    Keyword Arguments:
        suffix {str} -- suffix in the filename (default: {None})
                        This serves as the identifier of the current
                        state of the model
                        If not provided, the current timestamp is used
    """
    # generate default suffix if needed
    if suffix is None:
        suffix = datetime.datetime.now().strftime("%b_%d_%Y_%H_%M_%S")

    # serialize and write
    with open(fname + '_' + suffix + '.cpkl', 'wb') as f:
        cloudpickle.dump(model, f)


def load_model(fname):
    """Deserializes and loads a dask or sklearn model

    Arguments:
        fname {str} -- path or filename (in current dir) of serialized model
    """
    with open(fname, 'rb') as f:
        model = cloudpickle.load(f)
    return model
