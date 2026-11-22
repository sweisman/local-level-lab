# Qualify scoring for the four repeat-turn forecasts

On each [bound input](ESA_REPEAT_TURN_INPUT_RESULT.md), keep two error
descriptions for the same forecast target. Seal the training identity,
later query times, conditional path, native covariance factor and
angular exposure before reading the later receiver positions. The
scorer takes the expected seal hash from the execution receipt and
checks the original times before it accepts those positions.

Use the earlier 200/120 forecast's working native variance scales
from the [earlier scoring receipt](esa-fast-force-transfer-earlier.json).
Compare that covariance on its own, with an independent constant
acceleration term, with a 15-second maneuver response, and with both.
Each added term uses the earlier 0.001 m/s² working reference. Treat
these sizes as fixed development assumptions and preserve both terms
separately. Unsigned angular exposure creates horizontal uncertainty
in either direction, so the same rule can be used for left and right
turns. The scored path is the same under all four covariance choices.

Report north, east and height error and the joint Gaussian score,
including the covariance normalization. Qualify the calculation with
known covariance, a generated ensemble, a reversed turn, and altered
timestamps or forecast bytes. The qualification uses one numerical
thread and at most 4,096 independent generated error draws. It opens
no observed inputs and makes zero trajectory fits. Aircraft accuracy,
physical model comparison, optimizer qualification and a resumable
execution freeze are separate from this scoring check.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_repeat_turn_scoring request
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m pytest -q \
  analysis/tests/test_esa_repeat_turn_scoring.py \
  --junitxml=docs/prediction-observed-development/esa-repeat-turn-scoring-tests.xml
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_repeat_turn_scoring verify
```
