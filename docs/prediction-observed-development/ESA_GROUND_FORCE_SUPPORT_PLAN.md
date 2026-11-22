# Can two ground stops constrain the airborne calibration?

Keep both [receiver-selected stops](SECOND_GROUND_INTERVAL_RESULT.md)
from opened ESA recording 187. Decode their logged acceleration and
temperature from the verified original. Report the two mean force
vectors, their separation angle, and the spread of complete minute
means within each stop. Receiver speed established the selection.
Attitude, absolute specific force and stability of calibration between
the stops are open.

Each stop supplies a different unknown local force magnitude. With
orientation and these two magnitudes both free, the two stop means do
not independently constrain the accelerometer calibration. Test a
more favorable case by treating both corrected magnitudes as known
exactly at their nominal values. Use the derivative of each magnitude
with respect to the same accelerometer biases and gains as the saved
400-report airborne fit. Project out the two exact constraints before
repeating the [unrestricted training-design check](ESA_FITTED_SCALE_SUPPORT_RESULT.md)
for steady acceleration. Use all three archived model tangents and
the same rank tolerances of 10⁻⁸ and 10⁻¹⁰.

One original-file hash pass, at most 1,365,154 decoded samples, six
anchored and six free local projections, one numerical thread, and
zero nonlinear fits or native calls. Use the original stops, no later
receiver outcomes and no reserved group. Exact force magnitudes provide
a sensitivity limit for this particular pair of constraints. They are
not physical calibration observations in this dataset.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_ground_force_support freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_ground_force_support replay
```
