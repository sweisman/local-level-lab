# Why small gyro errors can grow into position errors

The running noise test asks whether a fitted model can predict later positions
while its IMU inputs contain random errors. An **IMU (inertial measurement
unit)** measures angular motion and specific force. An angular error can tilt
the reconstructed direction of gravity, creating an acceleration error that
accumulates into a position error.

A simple calculation gives a useful scale. Assume a level platform, constant
gravity, small angular errors, a perfectly known initial state and independent
continuous white noise. There is no later position correction. This example
omits changing bias and receiver error; it is not a reconstruction of the
turning, climbing aircraft.

For gyro noise amplitude \(q\), gravity \(g\) and elapsed time \(T\), the
position variance on **each horizontal axis** is

\[
\operatorname{Var}[p(T)]=g^2q^2\int_0^T\frac{(T-s)^4}{4}\,ds
=\frac{g^2q^2T^5}{20}.
\]

Using the stress test's declared gyro amplitude, **0.02°/√hour**, and
\(g=9.80665\,\mathrm{m/s^2}\), this gives **40.8 m standard deviation per
horizontal axis after 400 seconds**. At one-second horizons from 1 through
400 seconds, the square root of the expected mean horizontal squared error
is **23.7 m**. That quantity is not the expected value of a realized RMS.
The corresponding accelerometer-only endpoint scale, at the declared
\(0.0002\,\mathrm{m/s/\sqrt{s}}\), is 0.924 m per axis.

The example shows why a noisy control can miss a 10 m horizontal RMS target
even when arithmetic and initialization are accurate. It does not prove a
lower bound for every estimator, predict the outcome of a particular test
case, or measure the real instrument's noise. The assumed amplitudes remain
stress settings, not hardware specifications.

Later errors also share the same earlier noise history. They are correlated;
400 later epochs do not provide 400 independent error samples. A useful
prediction-error model must account for that accumulation and correlation.
The current accuracy limit and all failures remain unchanged. Any revised
method needs separate qualification under its stated stochastic assumptions.

The reusable [analytic kernel](../../analysis/lll/inertial_error_budget.py)
computes both marginal and cross-time covariance. Ten local software checks
include independent numerical integration of the impulse responses, symmetry,
zero horizon, invalid inputs and temporal correlation. Reproduce them with:

```sh
~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 --reserved-threads 3 -- ~/venv/bin/python -m pytest -q analysis/tests/test_inertial_error_budget.py
```

[Noise-test plan](PLAN.md) · [Saved rate variation](../esa-training-rate-variation/README.md) ·
[Prediction error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md).
