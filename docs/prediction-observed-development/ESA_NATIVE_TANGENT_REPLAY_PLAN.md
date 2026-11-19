# Reproduce the ESA forecast and save its calibration derivatives

Use the first passing specified-field fit for the profiled increment-error
case in the sealed 400-training, 120-prediction development matrix. The only
purpose is to recover the change in the predicted path for small changes in
each of the 27 fitted quantities. A later check can then ask how calibration
directions that resemble one another in training affect the predicted path.

- Use the fixed calibration, original clock, original increments and
  earlier receiver positions. Later query times are needed for propagation.
- Verify the archived source and compiler receipt. Require exact agreement
  with the saved predicted coordinates and earlier coordinate residuals.
  Retain the full derivative array only after this check passes.
- Allow one native sweep, zero optimizer starts, one numerical thread and
  a 120-second cooperative wall allowance. A charged sweep stays charged.
- Use zero withheld receiver positions and zero protected flight records.
  This check neither estimates uncertainty nor tests a physical model.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_native_tangent_replay prepare
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.studies run \
  data/esa-native-tangent-replay-v1-20261118 --reserved-threads 0
```
