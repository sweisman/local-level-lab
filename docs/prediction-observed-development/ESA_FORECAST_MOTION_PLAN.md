# Compare the score blocks with recorded aircraft motion

Use the same four 30-report blocks in each frozen 120-report ESA
development holdout. Report ground-track turning, horizontal acceleration,
ascent rate and speed from the recorded receiver velocities. Summarize
body angular rate and specific force using time-weighted raw increments
from the original prepared forecast input. Add satellite count, dilution
of precision and reported east position precision as receiver context.

Compare the movement and receiver conditions across all eight blocks
with the already sealed east-ordered and east-position error shares.
Distinguish uncorrected ground course from instrument heading and the
recorded angular-rate magnitude from aircraft rotation alone. These
block summaries can suggest diagnostic tests and cannot identify the
source of forecast error.

The replay uses one thread, the original prepared intervals and the same
receiver observations. There are no new fits, original-file opens, native
sweeps or reserved-flight reads.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.forecast_motion_context freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.forecast_motion_context replay
```
