# Release and compare the steady-course forecasts

Require all 16 planned starts to reach a terminal outcome. Select the
lowest converged training cost in each window and error description.
Start 0 wins an exact tie. If the selected forecast is missing, retain
the missing result. Verify the selected forecasts' seals, training
hashes and later clocks before decoding a later GPS position.

Repeat the fixed four-allowance score. For each matched turn and control,
report the gain from adding the turn allowance to the native covariance
and to the covariance with steady uncertainty already included. A
positive turn-minus-control gain means the allowance helped more in the
turn. Retain angular exposure and all missing results. The two error
descriptions share measurements and the four pairs share one recording.

The following qualification request replaces the initial three-test
workflow check in the [forecast plan](ESA_STRAIGHT_CONTROL_FORECAST_PLAN.md).
It includes the matched-score and receiver-release checks.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_straight_control_forecast request
env PYTHONPATH=analysis PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ~/venv/bin/python -m pytest -q \
  analysis/tests/test_esa_straight_control_forecast.py analysis/tests/test_esa_straight_control_release.py \
  --junitxml=docs/prediction-observed-development/esa-straight-control-forecast-release-tests.xml
```

After the forecast study closes, run
`lll.esa_straight_control_release release` and then
`lll.esa_straight_control_release score`, each with the manifest hash
from preparation passed as `--manifest-sha256`. Use the numerical guard
with the frozen four one-thread workers. The second command verifies
the saved release before opening later positions.
