# Check support for separate drift and maneuver scales

Use the verified factors and inertial inputs of the two
[already scored forecasts](ESA_NATIVE_ROLLING_TRANSFER_RESULT.md)
to check whether the three covariance scales have distinguishable
effects. The components are the archived covariance, persistent
acceleration and the [motion response](ESA_MOTION_ERROR_LAW_RESULT.md).
For each time cut and each IMU error description, compute the local
Gaussian information in the three log variances. Remove the other
two component directions when reporting the information in one
component. Use independent acceleration reference standard deviations
of 0.0001 and 0.001 m/s². The archived covariance uses the earlier
holdout's common working scale. This checks a fixed covariance
design, leaving actual errors and parameter uncertainty open.

Check the three previously selected recording-187 development windows
for actual maneuver exposure in their earlier portions. Verify both
original files by hash. Within the fixed receiver query boundaries,
use the documented forward/starboard/down logged angular rates with
left-endpoint integration and the frozen 1°/s exposure definition.
Use the first inertial timestamp at or beyond the earlier cut only
to close the final interval. Decode no rate at or beyond that cut.
Keep the existing selections and report exposure in chronological
quarters. No forecast error is used for this calculation.

One numerical thread, eight covariance information calculations,
one hash pass over each source file, at most 723,000 decoded raw
inertial rows and exactly 2,400 earlier receiver queries are allowed.
There are no new trajectory fits, native sweeps, prospective
holdout positions or reserved-flight reads.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_component_preflight freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_component_preflight replay
```
