# Python Module Interface Design


## Context and Problem Statement

One of the decision outcomes of [ADR #0001](0001-handling-dependencies-downstream.md) was that the trained models and other ML related parts of the code should be removed from the Ceph tree and put in a separate python module instead. Ceph (and other end users) can then simply import this module and run inference on their SMART data. The goal of this ADR is to establish the interface of this module, so that it is easy to integrate into and use within the Ceph codebase.


## Decision Drivers

* End user experience / workflow
* Integration with Ceph
* Implementation complexity
* Ease of adding, removing or replacing models


## Considered Options

### For Input Format

1. Raw `smartctl` output json.
2. Json with keys `vendor`, `model_name`, `user_capacity`, `smart_x_raw`, `smart_x_normalized`, created from the raw `smartctl` output.

### For Output Format
1. An enum member e.g. `DiskHealthStatus.WARNING` (same idea as [HTTPStatus](https://github.com/python/cpython/blob/ab4da079232356e781743b2782148bc7c03f1ee3/Lib/http/__init__.py#L5) enum).
2. Strings `good`, `warning`, `bad`.
3. A result dictionary containing at least the following keys:
    - `message`: string; will hold a short, user-friendly description of the prediction result (one line that can be displayed in `ceph device ls`)
    - `is_healthy`: boolean; will be `True` if the device is healthy (GOOD), or `False` otherwise (BAD/WARNING)

    It may contain any other keys that are unique to each prediction model. For example, the result of "redhat" prediction model can contain `status` (to hold the enum status `GOOD`/`WARNING`/`BAD`), `life_expectancy_day_min`, `life_expectancy_day_max`, etc.

### For Where to Store Trained Models

1. In the python module itself.
2. On a GitHub repo or MLflow server or s3 bucket. Create a "ModelStore" class to connect to and pull data from such platforms.

### For Running Inference

1. Manually import the desired predictor, and then run inference.
```python
from disk_health_predictor import RHDiskHealthClassifier

model = RHDiskHealthClassifier()
model.predict(input_data)
```
2. Import the desired predictor by passing an arg to a [factory method](https://www.tutorialspoint.com/python_design_patterns/python_design_patterns_factory.htm), and then run inference. If not provided by user, the `predictor_name` arg can be set via a helper function `get_optimal_predictor_name` that determiens the most suitable predictor based on vendor, model, and type (hdd, ssd, nvme) of disk.
```python
from disk_health_predictor import DiskHealthClassifierFactory

# option 1: pass name explicitly
model1 = DiskHealthClassifierFactory().create_predictor("redhat")
model1.predict(input_data)

# option 2: let the helper func determine name
predictor_name = DiskHeathClassiferFactory().get_optimal_predictor_name(disk_spec)
model2 = DiskHealthClassifierFactory().create_predictor(predictor_name)
model2.predict(input_data)
```

## Pros and Cons of the Options

### For Input Format

#### Option 1

* Good, because does not require user to process `smartctl` json output, and instead offloads this processing / reformatting to the python module.
* Good, because leaves the door open in future for building models based on other `smartctl` fields not used by current models.

#### Option 2

* Good, because input is a clean, simple, non-nested json.
* Bad, because requires users to do process / reformat `smartctl` json on their own.

### For Output Format

#### Option 1

* Good, because health statuses will be well defined and would not be able to take invalid values.

#### Option 2

* Bad, because there it would be possible for health status to take invalid values (i.e. there are no strict rules on what values a string can take).
* Bad, because additional processing might have to be done on output (e.g. `prediction.lower()=="warning"` instead of `prediction=="warning"`)

#### Option 3

* Good, because provides flexibility in format and level of detail in model output
* Good, because will make serialization simpler

### For Where to Store Trained Models

#### Option 1

* Good, because works for users running Ceph in disconnected environments.
* Good, because does not rely on additional libraries to connect to storage platforms.
* Bad, because bloats the size of python module.

#### Option 2

* Good, because provides flexibility in where data scientists can store models.
* Good, because keeps the size of the python module reasonable.
* Good, because provides modularity (i.e. download only those models which user wants).
* Bad, because will not work for users running Ceph in disconnected environments.
* Bad, because introduces more complexity in user workflow.

### For Running Inference

#### Option 1

* Good, because no intermediate steps have to be done to init models.
* Bad, because need to know what model to use at runtime.

#### Option 2

* Good, because allows dynamic instantiation using arguments, which will be the case for Ceph.
* Good, because this is essentially the [workflow](https://github.com/ceph/ceph/blob/9ab9cc26e200cdc3108525770353b91b3dd6c6d8/src/pybind/mgr/diskprediction_local/predictor.py#L44) the Ceph module uses currently.
* Good, because allows us to select predictor dynamically based on the disk, in cases where user doesn't explicitly specify which preditor to use.


## Decision Outcome

Use option #1 for input format, option #3 for output format, option #1 for storing models, and option #2 for running inference. The updated workflow in Ceph module would then look like this
```python
# in ceph/src/pybind/mgr/diskprediction_local/module.py
from disk_health_predictor import DiskHealthClassifierFactory, DiskHealthStatus

def _predict_life_expentancy(self, devid: str) -> str:
    # get raw smartctl json
    r, outb, outs = self.remote("devicehealth", "show_device_metrics", devid=devid, sample="")
    health_data = json.loads(outb)

    # initialize model as per args (self.predictor_model = "redhat")
    clf = DiskHealthClassifierFactory().create_predictor(self.predictor_model)

    # predict
    health_estimate = clf.predict(raw_smartctl_json)
    # Output: {'is_healthy': False, 'message': 'Disk will fail within 2 weeks', 'status': DiskHealthStatus.BAD, 'life_expectancy_day_min': 0, 'life_expectancy_day_max': 14}

    return health_estimate

def predict_all_devices(self) -> Tuple[int, str, str]:
    self.log.debug("predict_all_devices")
    devices = self.get("devices").get("devices", [])
    for devInfo in devices:
        ###
        # SOME CODE HERE
        ###
        result = self._predict_life_expentancy(devInfo["devid"])
        if result["status"] != DiskHealthStatus.UNKNOWN:
            life_expectancy_day_min = result["life_expectancy_day_min"]
            life_expectancy_day_max = result["life_expectancy_day_max"]
        else:
            life_expectancy_day_min = 0
            life_expectancy_day_max = 0
```
