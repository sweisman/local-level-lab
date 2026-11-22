# Test whether fast variation explains the ESA force discrepancy

Use the same 96 non-overlapping supports and receiver time weights as
the [matched force comparison](ESA_MATCHED_FORCE_RESULT.md). First
reproduce its original logged force magnitudes. Then divide each support
into nested 0.1-second and 1-second bins, starting at the first report.
In each bin average the recorded three-axis force before taking its
magnitude. Compare this with taking magnitudes before averaging. The
gap measures how much rapid changes in force direction increase the
reported magnitude and can include actual motion, vibration and noise.

Use the logged angular-rate magnitude to calculate an orientation-only
upper bound on that gap, assuming a fixed external force direction
within each bin, accurate relative angular motion and the same sample
holds. Use this as a diagnostic of the recorded channels. It does not
bound all real aircraft rotation or identify the motion's physical source.

Compare the changed magnitudes with the same sealed receiver values.
Transfer the same descriptive median offset from the other two windows
to each window for each averaging order. Keep all 96 centers, including
the previously identified high-disagreement interval. Allow one hash
pass over each original, 2,400 earlier receiver reports, at most 723,000
decoded inertial samples, one thread and zero trajectory fits or native
steps. Later receiver positions and reserved groups are outside scope.

This check can localize fast variation that a smooth receiver fit omits.
It cannot distinguish aircraft vibration from sensor noise or
calibration, or turn the logged gyro into an independent attitude
reference. Use the result for error-model development on this flight.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_force_variation freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_force_variation replay
```
