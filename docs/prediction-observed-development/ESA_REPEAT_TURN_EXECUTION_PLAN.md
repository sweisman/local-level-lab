# Execute the training-only repeat-turn forecasts

Bind the [four prepared bundles](ESA_REPEAT_TURN_MATERIAL_RESULT.md)
with the shared study launcher. Each window uses two IMU error
descriptions and starts 0 and 1, for **16 primary fit tasks**. Use
the earlier specified-field globe reference with the processing fraction
profiled, the same calibration bounds, and a 200-evaluation ceiling.
This is a test of prediction errors through maneuvers on one development
flight. A model comparison requires its own matched study.

Each task fits the earlier 400 receiver rows and predicts the same
120 saved query times through the original IMU increments. A converged
fit must reproduce its earlier Gaussian cost and determinant when the
error operator is extended to the forecast horizon. Use that operator
to seal the conditional receiver path, its joint native covariance
factor and the later angular exposure. Keep failed starts and their
charges. The forecast worker and its recovery inputs hold no later
receiver positions.

Allow four one-thread workers and at most eight hours of original
wall time, with up to 900,000 native calls and 45.1 billion packet
visits per task. This retains the earlier fit allowance and adds one
bounded whole-path covariance pass. Resume only unfinished technical
work under a separate allowance of at most four additional charged
starts, one per interrupted task, and four hours. Preserve terminal
fit failures and verify original charges before any continuation.

Once all planned outcomes have sealed, choose the primary start for
each window and IMU law using the lowest converged training cost, with
start order breaking ties. The separate scoring step must check this
choice and each forecast seal before opening the later receiver
positions. Apply the [fixed scoring rule](ESA_REPEAT_TURN_SCORING_RESULT.md)
and report horizontal and height error alongside the covariance scores.
Independent aircraft coverage remains open.

The adapter qualification checks the exact task set, rejects unapproved
input fields before access, and uses generated forecast and interruption
controls. Stage the manifest under its verified software and recovery
evidence before launching the numerical fits.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 4 --threads 1 -- ~/venv/bin/python -m lll.esa_repeat_turn_execution request
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 4 --threads 1 -- ~/venv/bin/python -m pytest -q \
  analysis/tests/test_esa_repeat_turn_execution.py \
  analysis/tests/test_esa_conditional_forecast_v3_study.py \
  --junitxml=docs/prediction-observed-development/esa-repeat-turn-execution-tests.xml
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m pytest -q \
  analysis/tests/test_task_resume.py \
  --junitxml=docs/prediction-observed-development/esa-repeat-turn-recovery-tests.xml
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 4 --threads 1 -- ~/venv/bin/python -m lll.esa_repeat_turn_execution prepare
```
