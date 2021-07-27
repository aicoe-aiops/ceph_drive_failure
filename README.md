# Ceph Hard Drive Failure Prediction
*A comprehensive machine learning project for predicting whether a hard disk will fail within a given time interval*

More than [2500 petabytes](https://www.domo.com/learn/data-never-sleeps-5?aid=ogsm072517_1&sf100871281=1) of data is generated every day by sources such as social media, IoT devices, etc., and every bit of it is valuable. That’s why modern storage systems need to be reliable, scalable, and efficient. To ensure that data is not lost or corrupted, many large scale distributed storage systems, such as [Ceph](https://ceph.io), use use erasure-coded redundancy or mirroring. Although this provides reasonable fault tolerance, it can make it more difficult and expensive to scale up the storage cluster.

This project seeks to mitigate this problem using machine learning. Specifically, the goal of this project is to train a model that can predict if a given disk will fail within a predefined future time window. These predictions can then be used by Ceph (or other similar systems) to determine when to add or remove data replicas. In this way, the fault tolerance can be improved by up to an order of magnitude, since the probability of data loss is generally related to the probability of multiple, concurrent disk failures.

In addition to creating models, we also aim to catalyze community involvement in this domain by providing Jupyter notebooks to easily get started with and explore some publicly available datasets such as Backblaze Dataset and Ceph Telemetry. Ultimately, we want to provide a platform where data scientists and subject matter experts can collaborate and contribute to this ubiquitous problem of predicting disk failures.

* **[Get Started](docs/get-started.md)**

* **[Project Content](docs/content.md)**

* **[How to Contribute](docs/how-to-contribute.md)**

## Contact
This project is maintained by the AIOps teams in the AI Center of Excellence within the Office of the CTO at Red Hat. For more information, reach out to us at aicoe-aiops@redhat.com.
