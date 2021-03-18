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
* Con: Some users may be reluctant to send their disk health data to the service.

## Decision Drivers

* How would the solution affect user experience?
* How difficult would it be to maintain the solution, long term?
* What would need to happen if we want to use a different pacakge?
* What would need to happen if we want to increase model complexity?
* What would need to happen if we want to add, remove or replace models?

## Decision Outcome [to be discussed]

Suggested choice: Option #1 for current models, Option #5 for future models

* The only package missing from EPEL8 that the current models require is `scikit-learn`. So explicitly
running  `pip install scikit-learn` during container build should be a quick fix, even though it deviates from a
current Red Hat-internal workflow.

* Since only one package is being `pip install`-ed, this likely won't introduce any "package interdependency" issues.

* Going forward, we can enforce a strict rule that these "baked-in" models used by the `diskprediction_local` module must not use any ML libraries other than `scikit-learn`. This limits the types of models that can be used, but it makes downstream packaging and model integration easier. Less accurate model is better than no model at all.

* Going forward, we can deploy the more complex models (e.g. survival analysis, neural networks, etc.) as a service that the `diskprediction_cloud` module can query. Users who want more accurate predictions than what the "local" models can provide, should send a query to this service along with their disk health data (sensitive info removed).
