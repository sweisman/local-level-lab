# Prepare training-only inputs for the repeat-turn forecasts

Prepare the four windows from the [repeat-turn input receipt](ESA_REPEAT_TURN_INPUT_RESULT.md)
using the previously verified original sources and the same linear
point-rate conversion. Require identical raw, increment, training
prefix, receiver and clock hashes. Package only constructed inertial
increments through the prediction end, the earlier 400 receiver rows,
and all 520 query times. Later receiver positions are outside the package.
The same material is available to both IMU error descriptions.

Allow one pass per original source, up to 628,000 decoded IMU points
and constructed intervals, at most 48 MiB of staged files, one thread,
and zero native calls or optimizer starts. Verify the saved material
using its hashes without rereading either original. The existing
forecast engine and recovery tests are checked separately. An execution
manifest must still bind its exact forecast and continuation tasks and
allowances before the study can run.

The eventual comparison is an error study. Its designated reference is
the same specified-field globe with fitted processing fraction used in
the earlier covariance diagnostics. Keep the two fixed starts and both
IMU error descriptions. Compare the four fixed covariance choices
within each unchanged reference forecast. This comparison supplies no
shape or rotation decision. Report numerical failures and keep later
positions outside each training task and its recovery inputs.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_repeat_turn_material freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_repeat_turn_material stage
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_repeat_turn_material verify
```
