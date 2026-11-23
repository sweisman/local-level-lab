# Replay of withheld receiver observations

This development check asks whether saved simulation forecasts can be scored
against noisy receiver readings without running the fits again. The earlier
calibration scored against the simulated aircraft's exact positions. See its
[original result](../prediction-calibration-host-20261030/INTERPRETATION.md).

## Fixed scope

Use the first of the 299 calibration seeds and all 24 saved fits for that seed.
Use zero new fits, zero new seeds and one numerical thread. Leave all 181
original validation seeds and all aircraft data unopened.

Recreate the receiver errors from the original seed and law. Beyond the
training interval, continue the same noise process with the last training
coordinate transform, as in the existing generated receiver-target checks.
Check the original training noise and receiver rows by hash before scoring
any future observations. Compare the saved raw forecast with both the exact
positions and the reconstructed receiver readings using the same common
three-axis root mean square position error in metres.

The replay checks whether the archived inputs and forecasts are reusable for
a receiver-target score. A common raw forecast loss does not carry over the
old threshold or create a forecast that accounts for correlated receiver
errors. The archive fits each model to its own simulated truth. The fits
within a seed share random draws and provide no matched three-model query or
independent validation of a new loss.

## Reproduce

From the repository root, run both commands in order. The first writes or
verifies the source, environment and archive bindings before the second
opens the saved forecasts. Both write deterministic records and reject
changes to an existing record.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.prediction_receiver_replay freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.prediction_receiver_replay replay
```
