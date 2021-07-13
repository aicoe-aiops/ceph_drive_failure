# Table of Contents

This project consists of the following main workstreams:

- [Hard Drive Failure Prediction](#hard-drive-failure-prediction)
    - [Data Exploration](#Data-Exploration)
    - [Data Cleaning](#Data-Cleaning)
    - [Model Training](#Model-Training)
    - [End-To-End Pipeline](#End-To-End-Pipeline)
- [SMART Metric Forecasting](#smart-metric-forecasting)
    - [Univariate Models](#Univariate-Models)
    - [Multivariate Models](#Multivariate-Models)
- [Alternate Dataset Explorations](#alternate-dataset-explorations)
    - [Ceph Telemetry Dataset](#Ceph-Telemetry-Dataset)
    - [FAST Dataset](#FAST-Dataset)
- [Disk Health Predictor Library](#disk-health-predictor-library)


# Hard Drive Failure Prediction

In this workstream, we address the primary objective of the project i.e. creating disk failure prediction models using open source datasets. Specifically, we train classification models to classify a given disk's health into one of three categories - `good` (>6 weeks till failure), `warning` (2-6 weeks till failure), and `bad` (<2 weeks till failure). These disk health categories were defined this way to be consistent with the [existing setup in Ceph](https://github.com/ceph/ceph/blob/f8f7b865715987139d96e4baf41c82329dc19108/src/pybind/mgr/diskprediction_local/module.py#L271) provided by [DiskProphet](https://www.prophetstor.com/diskprophet/), a disk health prediction solution from ProphetStor. The input for these models is 6 days of [SMART](https://en.wikipedia.org/wiki/S.M.A.R.T.) data, which was also a design choice made to be compatible with the [existing setup](https://github.com/ceph/ceph/blob/f8f7b865715987139d96e4baf41c82329dc19108/src/pybind/mgr/diskprediction_local/module.py#L151).

The data used for training the models is the [Backblaze](https://www.backblaze.com/b2/hard-drive-test-data.html) dataset. It consists of SMART data collected daily from the hard disk drives in the Backblaze datacenter, along with a label indicating whether or not the drive was considered failed.

The following notebooks were created as a part of this workstream:

## Data Exploration

* [`smartctl_json_db_format_finder`](../notebooks/data_sources/backblaze/step0_smartctl_json_db_format_finder.ipynb): Understand the structure of json outpu by the `smartctl` tool.
* [`smartctl_json_db_to_df`](../notebooks/data_sources/backblaze/step0_smartctl_json_db_to_df.ipynb): Convert a nested `smartctl` json to a pandas dataframe.
* [`data_explorer`](../notebooks/data_sources/backblaze/step1_data_explorer.ipynb): Explore the contents and salient properties of the Backblaze dataset.

## Data Cleaning:

* [`data_cleaner_seagate`](../notebooks/data_sources/backblaze/step2a_data_cleaner_seagate.ipynb): Clean data available for seagate disks.
* [`data_cleaner_hgst`](../notebooks/data_sources/backblaze/step2b_data_cleaner_hgst.ipynb): Clean data available for hgst disks.

## Model Training:

* [`clustering_and_binaryclf`](../notebooks/data_sources/backblaze/step3a_clustering_and_binaryclf.ipynb): Explore clustering models and binary pass/fail classifiers.
* [`ternary_clf`](../notebooks/data_sources/backblaze/step3b_ternary_clf.ipynb): Explore ternary classifiers, i.e. models that classify disk health into "good", "warning", and "bad" as described above.

## End-To-End Pipeline:

* [`kaggle_seagate_end2end`](../notebooks/data_sources/backblaze/kaggle_seagate_end2end.ipynb): Entire ML pipeline, starting from data cleaning to feature engineering to model training, for seagate disks. Combines the results from each notebook in the above sections.
* [`kaggle_hgst_end2end`](../notebooks/data_sources/backblaze/kaggle_hgst_end2end.ipynb.ipynb): Entire ML pipeline, starting from data cleaning to feature engineering to model training, for hgst disks. Combines the results from each notebook in the above sections.


# SMART Metric Forecasting

The goal of this workstream is to create models that can forecast the values of individual SMART metrics into the near future. The idea here is that these forecasting models could be used in tandem with the disk health classifier models from above. Together, they can provide a more granular and detailed insight into what specific component is likely to fail for a given disk. Based on this information, the storage system operator or subject matter expert can manually decide whether or not to remove a hard disk drive from the storage cluster or datacenter, based on their unique failure tolerance level.

## Univariate Models
In this initial setup, we treat each SMART metric as an independent variable to forecast. That is, we train univariate forecasting models for each (significant) SMART metric.

* [Notebook](../notebooks/experimental/forecast_smart_metrics.ipynb)

## Multivariate Models
In this subsequent setup, we take into account the interactions between various SMART metrics. That is, we train multivariate forecasting models to predict how all the SMART metric values will change together in the near future.

* [Notebook](../notebooks/experimental/multivariate_forecast_smart_metrics.ipynb)


# Alternate Dataset Explorations

Most of the work done in this project is based on the Backblaze dataset since it was the only large, publicly available, and well-curated dataset at the time. However, since this data is collected from just one company with a specific usage (backup), it might not be able to capture the various usage patterns of real Ceph users. Fortunately, there have been other recent efforts in academia and industry towards collecting more detailed disk health data, that help create better disk failure prediction models. Of these data sources, we investigate the following two in this workstream.

## Ceph Telemetry Dataset

The Ceph team has been collecting anonymized SMART metrics from their users. We have worked with them to make this data publicly available. Furthermore, we have created an exploratory notebook that walks you through accessing this data, highlights the main features of this data, and compares it with the Backblaze dataset.
* [Ceph Telemetry Data](https://kzn-swift.massopen.cloud/swift/v1/devicehealth/)
* [Walkthrough notebook](../notebooks/data_sources/telemetry/step0_EDA.ipynb)

## FAST Dataset

Recent [research](http://codegreen.cs.wayne.edu/wizard/#Publication) suggests that incorporating disk performance and disk location data with SMART metrics can be valuable in analyzing disk health. Specifically, [this](https://www.usenix.org/conference/fast20/presentation/lu) paper claims to achieve improvements in disk failure prediction models, when using these additional features. In this effort, we explore the FAST dataset and evaluate the tradeoffs between model performance gain and overhead of collecting additional metrics from users.

- Exploratory notebook (forthcoming)


# Disk Health Predictor Library

The goal of this workstream is to create an open source python module containing the models trained in this project. The goal is to make these models easily accessible and usable by everyone, not just Ceph users. This way, anyone can run inference on their own storage system using the models built in this project.
