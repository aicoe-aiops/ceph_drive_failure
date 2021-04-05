"""Module to test models by emulatating disk prediction workflow in ceph."""
import os
import pickle
import datetime
from tqdm import tqdm

from sklearn.metrics import classification_report, confusion_matrix

from predictor import RHDiskFailurePredictor, PSDiskFailurePredictor

# import warnings
# warnings.simplefilter(action="ignore")  # scikit learn throws version warnigns

# how many days in each
WEEK = 7
BAD_RUL_MAX = 2 * WEEK
WARNING_RUL_MAX = 6 * WEEK


def get_diskfailurepredictor_path():
    """Get abolute path of predictor module."""
    path = os.path.abspath(__file__)
    dir_path = os.path.dirname(path)
    return dir_path


def preprocess_health_data(health_data, reverse):
    """Process raw SMART metrics according to input requirements of the prediction models."""
    predict_datas = []
    o_keys = sorted(health_data.keys(), reverse=reverse)
    for o_key in o_keys:
        # get values for current day (?)
        dev_smart = {}
        s_val = health_data[o_key]

        # add all smart attributes
        ata_smart = s_val.get("ata_smart_attributes", {})
        for attr in ata_smart.get("table", []):
            # get raw smart values
            # FIXME: this skips the 0 valued data
            if attr.get("raw", {}).get("string") is not None:
                # TODO: why are we looking at the str value and then if
                # that is not found then int. why not get int directly?
                if str(attr.get("raw", {}).get("string", "0")).isdigit():
                    dev_smart["smart_%s_raw" % attr.get("id")] = int(
                        attr.get("raw", {}).get("string", "0")
                    )
                else:
                    if (
                        str(attr.get("raw", {}).get("string", "0"))
                        .split(" ")[0]
                        .isdigit()
                    ):
                        dev_smart["smart_%s_raw" % attr.get("id")] = int(
                            attr.get("raw", {}).get("string", "0").split(" ")[0]
                        )
                    else:
                        dev_smart["smart_%s_raw" % attr.get("id")] = attr.get(
                            "raw", {}
                        ).get("value", 0)
            # get normalized smart values
            if attr.get("value") is not None:
                dev_smart["smart_%s_normalized" % attr.get("id")] = attr.get("value")
        # add power on hours manually if not available in smart attributes
        if s_val.get("power_on_time", {}).get("hours") is not None:
            dev_smart["smart_9_raw"] = int(s_val["power_on_time"]["hours"])
        # add device capacity
        if s_val.get("user_capacity") is not None:
            if s_val.get("user_capacity").get("bytes") is not None:
                # TODO: should this be converted to GB to make computation more correct and easier?
                dev_smart["user_capacity"] = s_val.get("user_capacity").get("bytes")
            else:
                # TODO: change to info logging level
                print("Unable to read user_capacity")
        # add device model
        if s_val.get("model_name") is not None:
            dev_smart["model_name"] = s_val.get("model_name")
        # add vendor
        if s_val.get("vendor") is not None:
            dev_smart["vendor"] = s_val.get("vendor")
        # if smart data was found, then add that to list
        if dev_smart:
            predict_datas.append(dev_smart)
    return predict_datas


def is_correct(rul, pred):
    """Return a good/warning/bad prediction based on remaining useful life prediction."""
    if pred == "good":
        return rul >= WARNING_RUL_MAX
    elif pred == "warning":
        return (rul >= BAD_RUL_MAX) and (rul <= WARNING_RUL_MAX)
    elif pred == "bad":
        return rul <= BAD_RUL_MAX
    else:
        return False


if __name__ == "__main__":
    # sort data in descending order
    REVERSE = False

    # init and predict using just one day
    predictor_model = "redhat"
    if predictor_model == "redhat":
        obj_predictor = RHDiskFailurePredictor()
    elif predictor_model == "prophetstor":
        obj_predictor = PSDiskFailurePredictor()
    else:
        print("invalid input for predictor name")

    ret = obj_predictor.initialize(
        "{}/models/{}".format(get_diskfailurepredictor_path(), predictor_model)
    )
    if ret is not None:
        print("Error initializing:", ret)

    # get data to predict on, in a format like ceph
    WORKING_TEST_SAMPLES = "/home/kachauha/Documents/ceph_drive_failure/q1_2019_working_drive_datas_1579876241.pkl"
    FAILED_TEST_SAMPLES = "/home/kachauha/Documents/ceph_drive_failure/q1_2019_failed_drive_datas_1579860481.pkl"

    PREDICTION_CLASSES = {"good": 0, "warning": 1, "bad": 2, "unknown": -1}

    with open(FAILED_TEST_SAMPLES, "rb") as f:
        # read in all serials worth of data
        all_sers_all_days_data = pickle.load(f)

    with open(WORKING_TEST_SAMPLES, "rb") as f:
        # read in all serials worth of data
        all_sers_all_days_data.update(pickle.load(f))

    # nmuber of days worth of data available
    time_window = 6

    # file to write results to
    with open(
        "results/results_{}_reverse{}_{}.txt".format(
            predictor_model,
            REVERSE,
            datetime.datetime.now().strftime("%b_%d_%Y_%H_%M_%S"),
        ),
        "w+",
    ) as results_fileobj:
        # predict serial by serial
        y_true = []
        y_pred = []
        tqdm_bar = tqdm(all_sers_all_days_data.items())
        for curr_ser, curr_ser_all_days_data in tqdm_bar:
            tqdm_bar.set_description("Serial {:16s}".format(curr_ser))
            # print("==================== Serial Number {:10s} ====================".format(curr_ser))

            # number of days worth of data available for this serial number
            num_days = len(curr_ser_all_days_data)
            if num_days < time_window:
                print("Less than 6 days of data for serial number {}".format(curr_ser))
                results_fileobj.write(
                    "Less than 6 days of data for serial number {}".format(curr_ser)
                )
                continue

            curr_ser_dates = sorted(curr_ser_all_days_data.keys())
            for i in range(0, num_days - time_window + 1):
                # remaining life as of current batch
                rul = num_days - i - time_window

                # dates to use for current predction
                curr_ser_curr_batch_dates = curr_ser_dates[i : i + time_window]

                # data corresponding to current batch
                health_data = dict(
                    (date, curr_ser_all_days_data[date])
                    for date in curr_ser_curr_batch_dates
                )

                # preprocess, predict, compare w/ gournd truth
                predict_datas = preprocess_health_data(health_data, REVERSE)
                pred = obj_predictor.predict(predict_datas).lower()

                # update ytrue and ypred
                if rul >= WARNING_RUL_MAX:
                    y_true.append(0)
                    # print('Actual = {:10s}\tPredicted = {:10s}'.format('good', pred))
                    results_fileobj.write(
                        "Actual = {:10s}\tPredicted = {:10s}".format("good", pred)
                    )
                elif rul >= BAD_RUL_MAX:
                    y_true.append(1)
                    # print('Actual = {:10s}\tPredicted = {:10s}'.format('warning', pred))
                    results_fileobj.write(
                        "Actual = {:10s}\tPredicted = {:10s}".format("warning", pred)
                    )
                else:
                    y_true.append(2)
                    # print('Actual = {:10s}\tPredicted = {:10s}'.format('bad', pred))
                    results_fileobj.write(
                        "Actual = {:10s}\tPredicted = {:10s}".format("bad", pred)
                    )
                y_pred.append(PREDICTION_CLASSES[pred])

        # calculate metrics
        confmat = confusion_matrix(
            y_true, y_pred, labels=list(PREDICTION_CLASSES.values())
        )
        report = classification_report(
            y_true,
            y_pred,
            labels=list(PREDICTION_CLASSES.values()),
            target_names=PREDICTION_CLASSES.keys(),
        )
        print(confmat)
        print(report)
        results_fileobj.write(str(confmat) + "\n")
        results_fileobj.write(report)
