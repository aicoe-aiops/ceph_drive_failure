# Ceph Drive Failure Prediction

## Overview
More than [2500 petabytes](https://www.domo.com/learn/data-never-sleeps-5?aid=ogsm072517_1&sf100871281=1) of data is generated every day by sources such as social media, IoT, commercial services, etc. Of this, a sizeable chunk is persisted in storage systems (HDDs and SSDs). To ensure that data is not lost or corrupted, large scale storage solutions often used erasure-coding or mirroring. However, these techniques become more difficult and/or expensive to deal with at scale.

This project aims to enhance [Ceph](https://ceph.io), a distributed storage system, by giving it the capability to predict the failure of storage devices well in advance. These predictions can then be used to determine when to add/remove replicas. In this way, the fault tolerance may be improved by up to an order of magnitude, since the probability of data loss is generally related to the probability of multiple, concurrent device failures.

## Dataset
The Backblaze Hard Drive dataset will be used for this project. This dataset consists of daily snapshots of basic information, SMART metrics, and status (failure label) for the hard drives in the Backblaze data center. Details about this dataset can be found [here](https://www.backblaze.com/b2/hard-drive-test-data.html). To learn more about the SMART system and SMART metrics, see [this](https://en.wikipedia.org/wiki/S.M.A.R.T.) Wikipedia article.

## Objective
The goal is to create predictive models using the Backblaze dataset to determine when a hard drive will fail. Ideally, the model should be able to predict the health of a hard drive in terms of "good" (>6 weeks till failure), "warning" (2-6 weeks till failure), and "bad" (<2 weeks till failure). This setup is similar to [DiskProphet](https://www.prophetstor.com/diskprophet/), a disk health prediction solution from ProphetStor.

At inference time, 6 days of SMART data (6 rows from the Backblaze dataset) will be available to feed to this multiclass classification model. How the model makes use of this is a design choice. It may predict on all 6 individually, or generate features using multiple days data, or use only the last day data, etc. For details on how this model would be integrated into Ceph (API, preprocessing at inference time, etc) see [this](https://github.com/ceph/ceph/tree/master/src/pybind/mgr/diskprediction_local).

**NOTE:** Although the end goal is a multiclass classifier, building a binary classifier ("no fail"/"fail") could be a good starting point in understanding the problem and setup. Additionally, data exploration and insightful analysis could also be useful. These would be welcome contributions to this project as well.

## Notebooks/Kernels
The following are some notebooks to get started or to use as utils:  
`data_explorer.ipynb`  
`data_cleaner_*.ipynb`  
`clustering_and_model_exploration.ipynb`  
`multiclass_clf.ipynb`  

## Contact
Karanraj Chauhan  
Software Engineer, AI Center of Excellence - Office of the CTO  
Red Hat, Inc.