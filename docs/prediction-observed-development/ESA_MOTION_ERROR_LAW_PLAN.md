# Test persistent acceleration drift and a separate maneuver response

Use the sealed recordings and forecasts from the
[two 120-report holdouts](ESA_NATIVE_ROLLING_TRANSFER_RESULT.md)
on ESA development recording 187. Keep the recorded-increment and
sampled-rate noise descriptions. Keep all fitted paths and native
conditioning factors fixed.

Compare the archived covariance with two independent additions and
with both additions together.

- **Persistent acceleration** starts at the cut and gives position
  error proportional to elapsed time squared on each of the three axes.
- **Maneuver response** adds a horizontal acceleration shock at each
  forecast query where the previous interval's time-weighted logged
  body angular-rate RMS exceeds 1°/s. Shock variance is proportional
  to the integral of squared angular rate above that interval's
  threshold energy. Each acceleration shock decays over 15 seconds.
  Its position response integrates the acceleration and resulting
  velocity error. No response precedes the triggering query.

Both shapes use an exploratory reference acceleration standard
deviation of 0.001 m/s², with the maneuver term using the exposure
factor above. The threshold, decay and reference acceleration are
stress-test settings. They propose a covariance shape without claiming
a measured instrument limit. Only recorded inertial increments and
query times set the triggers.

Set one overall variance multiplier for each alternative from the
earlier held-out window. Seal it, then score the later window using
the same scale and the full conditional covariance. Compare squared
error and the Gaussian negative log score, which penalizes added
uncertainty. On the separate previously scored 400-report straight
holdout, check how much height error the persistent quadratic
direction alone can account for in physical metres. That last check
is retrospective and estimates the best coefficient for one shape.

The four window/law combinations use at most 16 covariance spectra
and one additional scalar projection on one thread. There are no new
native sweeps, trajectory fits or protected-flight reads. Qualifying a
law for aircraft still requires independent validation.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_motion_error_transfer freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_motion_error_transfer earlier
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_motion_error_transfer compare
```
