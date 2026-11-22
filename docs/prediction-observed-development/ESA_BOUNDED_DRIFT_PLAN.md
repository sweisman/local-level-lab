# Can the calibration box separate steady acceleration error?

The [unrestricted projection](ESA_FITTED_SCALE_SUPPORT_RESULT.md) found
little separate information about steady acceleration. This check uses
the three sealed ESA 400-report training designs to test whether the
earlier local step limit changes that conclusion. All three models use
the same underlying flight interval.

In each design, convert a constant acceleration of 0.0001 or 0.001 m/s²
into displacement from the first earlier receiver fix. Test north, east
and up with both signs. Whiten the displacement using the archived
training covariance and find the closest position change the training
tangent can make. Compare two cases:

- Allow the full set of calibration parameters to move within the original
  parameter box and the previously used local radius of 0.1
  in normalized coordinates.
- Use those same constraints and fix the three accelerometer biases and
  the gravity adjustment at their archived values. This is a hypothetical
  check of what independently knowing those quantities could buy.

Report the remaining fraction of squared displacement, the maximum
normalized step, variables at their bounds, and the gap between the
achieved result and a lower bound from convexity. Require that gap to
be no more than 10⁻⁵ of the unadjusted pattern energy to call an optimum
verified. Give uncertified cases their own disposition.

There are 72 bounded linear solves with up to 100 BVLS main-loop iterations each, one
numerical thread, and zero nonlinear fits or native propagations. The
inputs are training derivatives and covariance only. Actual receiver
residuals and future positions are not used as targets. The experiment
checks a local affine model and hypothetical patterns. Its calibration
box is a working assumption, and fixing parameters does not validate
the archived values.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_bounded_drift_support freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_bounded_drift_support replay
```
