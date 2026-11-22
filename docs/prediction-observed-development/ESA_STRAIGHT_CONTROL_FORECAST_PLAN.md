# Forecast positions on the steady-course controls

Use the [four preselected controls](ESA_STRAIGHT_CONTROL_PLAN.md) from
development recording 187. Start only after the
[input preparation](ESA_STRAIGHT_CONTROL_MATERIAL_PLAN.md) has sealed all
twelve input files. Bind the exact reference recipe from the archived
turn run. Fit the specified-field globe with the same processing and
calibration allowances, both inertial error descriptions, and starts
0 and 1. This yields 16 starts.

Fit on the first 400 GPS positions and carry the prediction through the
120 later query times. Seal the conditional path and covariance. Replay
the training score and retain all 27 fitted parameters. The runner uses
later inertial readings to propagate the path and measure angular
exposure. The later GPS positions stay withheld.

Use four workers on one thread each and the original eight-hour cap.
Each start retains the original 200-evaluation limit, 900,000 native
calls and 45.1 billion packet visits. The
[same recovery policy](ESA_REPEAT_TURN_RELEASE_RESULT.md) allows one
technical retry per interrupted task, at most four interruptions and
four hours under a separate allowance. Preserve all sealed passes and
failures.

Select forecasts by training cost before any later positions are read.
Compare the four fixed error allowances on the same predicted paths.
Report every planned case. These four controls answer a same-recording
question about when the turn allowance helps. They provide no flight
replication or absolute error calibration.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_straight_control_forecast request
env PYTHONPATH=analysis PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ~/venv/bin/python -m pytest -q \
  analysis/tests/test_esa_straight_control_forecast.py \
  --junitxml=docs/prediction-observed-development/esa-straight-control-forecast-tests.xml
```

After the material run closes, use the numerical guard with four
one-thread workers and `lll.esa_straight_control_forecast prepare`.
Preparation seals the inputs and budgets. Launch the study through
`lll.studies run` when the numerical threads are available.
