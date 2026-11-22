# How large would a new error need to be after the forecast cut?

Use the three sealed [native conditioned forecasts](ESA_CONDITIONED_CALIBRATION_RESULT.md)
on ESA recording 187, with their original covariance factors. Verify
the exact 120 receiver positions previously scored on that recording.
Keep the fitted calibrations, earlier receiver observations and
conditioned means fixed.

Try three independent error additions starting after the cut. The
first adds white position noise, the second adds a single random
position offset common to the later epochs, and the third adds a
position random walk. Use a metric based on the last earlier receiver
position to express all scales in metres per axis. For the walk,
quote the standard deviation at the end of the forecast.

Find the smallest added standard deviation, up to 100 m, that brings
the average squared standardized error down to one under each
candidate's archived covariance. Record whether an error mode leaves
some mismatch unchanged even as its variance grows. This is a
diagnostic benchmark. The required scale, if any, describes one error
shape and the existing forecasts without estimating a calibrated
accuracy or identifying the source of the error.

The replay is bounded to nine covariance spectra and fifty bisection
steps per spectrum on one thread. It uses no native sweeps, model fits,
new original-file reads or reserved flight groups.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_future_error_sensitivity freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_future_error_sensitivity replay
```
