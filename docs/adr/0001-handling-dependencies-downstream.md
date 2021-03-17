# Handling Model Dependencies in Downstream Packaging

## Context and Problem Statement

In both the OpenShift Container Storage and Red Hat Ceph Storage products, Ceph is delivered as a container image.
Generally, the build pipelines that create such product container images do so by first generating the required RPMs,
and then installing them during the container build.

One of the python packages that the disk failure prediction models on Ceph upstream require is
[scikit-learn](https://scikit-learn.org/stable). However, this package is not currently available as an RPM in EPEL8.
Therefore, it is not possible to install it (as an RPM) during container build. This in turn makes it difficult to
integrate the models into the end product and deliver them to the customer.

## Considered Options

1. Install the required python packages via `pip` (or similar tools) during container build.
2. Request maintainers to make their python packages available as RPMs. Install these during container build.
3. Manually create RPMs for the required python packages. Install these during container build.
4. Rewrite models in pure python, without using any machine learning packages.
5. Instead of integrating models into Ceph, deploy them as a service and have Ceph query this service.

## Pros and Cons of the Options

### Option 1

* Pro: Provides flexibility in what pacakges can be used.
* Pro: Provides opportunity to use Thoth recommended software stack to maximize security and performance.
* Con: This is not a typical Red Hat-internal method for container build pipelines.

### Option 2

* Pro: Installing RPMs during build conforms with the setup of existing build pipelines.
* Pro: Resulting RPMs can be used for any purpose by any user, not just for disk failure prediction in Ceph.
* Con: Maintainers of different packages may or may not have the time and resources to create RPMs.
* Con: It may be difficult to align RPM releases of different packages, and also releases of these RPMs with Ceph releases.

### Option 3

* Pro: Installing RPMs during build conforms with the setup of existing build pipelines.
* Pro: Resulting RPMs can be used for any purpose by any user, not just for disk failure prediction in Ceph.
* Pro: tchaikov (Kefu Chai) has already created the [RPM](https://github.com/ceph/ceph/pull/37513#issuecomment-796566516) for `scikit-learn`.
* Con: There may or may not be developers who work on creating RPMs for all of the required packages.

### Option 4

* Pro: Eliminates dependence on external packages.
* Con: Can be difficult to do for complex models.
* Con: Can turn into essentially "copying" model implementations from other libraries, which does not seem like a good practice.

### Option 5

* Pro: Eliminates dependence on external packages.
* Pro: Provides flexibility in what pacakges can be used.
* Pro: Provides opportunity to use Thoth recommended software stack to maximize security and performance.
* Pro: Ceph already had a module ([diskprediction_cloud](https://github.com/ceph/ceph/tree/nautilus/src/pybind/mgr/diskprediction_cloud)) designed to query an external service for failure predictions. But this had to be removed because the external service dropped support. Under this option, this module can be revived.
* Con: Disk failure prediction will not work "out of the box"; it would depend on the deployed service.
* Con: Under this option, the models will not be usable in a disconnected environment.
* Con: Some users may be reluctant to send their disk health data to the service.

## Decision Drivers

* How would the solution affect user experience?
* How difficult would it be to maintain the solution, long term?
* What would need to happen if we want to use a different pacakge?
* What would need to happen if we want to increase model complexity?
* What would need to happen if we want to add, remove or replace models?


## Decision Outcome

1. Use option #1 for the current setup.

    * The only package missing from EPEL8 that the current models require is `scikit-learn`. So explicitly running  `pip install scikit-learn` during container build should be a quick fix, even though it deviates from a typical workflow.

    * Since only one package is being `pip install`-ed, this likely won't introduce any "package interdependency" issues.

2. Going forward, remove the data preprocessing and ML inference code from Ceph tree, and create a separate python library containing this code. This will have the following benefits:
    * In addition to Ceph, others will be able to use these disk health prediction models too.
    * In future if we want to implement option #5 as an additional feature, this python library can also be used in that.
