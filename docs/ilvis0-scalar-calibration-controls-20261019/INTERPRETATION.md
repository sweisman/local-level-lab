# What calibration leaves in the scalar comparison

All **72 implementation controls passed**. They compare four constructed motion
histories, three generated truths, three comparison models and two instrument
orientation histories. They use no flight recordings. Each history lasts ten
minutes and has 121 exact epochs; these are not noisy receiver estimates.

## Straight motion loses its scalar distinction

The largest uncorrected eastbound magnitude gap was about 0.0301 m/s². After
projection against three gain, three offset and one gravity direction, every
eastbound residual was below 1.2 × 10⁻¹⁵ m/s². All suggested linear corrections
were inside the declared bounds.

That projection is first order. Its particular correction does not necessarily
give zero nonlinear error. The separate [constant-gain control](../ilvis0-measurement-contribution/CALIBRATION.md)
already supplies an exact nonlinear construction: a small isotropic gain change
alone erases the straight-leg scalar gap. Stationary controls correctly have
no model distinction before or after projection.

## Changing motion retains a local distinction

The changing-direction and climbing controls retain some difference outside
the local calibration directions. Their largest projected RMS values are about
0.00434 and 0.000769 m/s² respectively. These are mathematical discrepancies,
not noise-normalized evidence or measured sensor performance.

All 24 wrong-model changing-motion cases had suggested minimum-norm linear
corrections outside at least one bound. The report therefore leaves their
nonlinear-check fields empty. Applying or clipping those corrections would
neither preserve the local solution nor establish a valid bounded fit.

All seven calibration columns remain in the calculation. Stationary cases have
rank 4 or 6, eastbound cases rank 6, and the changing-motion cases rank 7 at the
declared relative tolerance of 10⁻¹⁰. Full local rank is not a statement about
global uniqueness, nonlinear model discrimination or robustness to receiver
and calibration uncertainty.

## What follows

The next gate is a separately bounded **nonlinear calibration control**, using
the same constructed histories and calibration region. It must check known
solutions, analytic derivatives, near-boundary cases and several declared starts;
preserve incomplete outcomes and test predicted-observation repeatability.
Report feasible residuals rather than interpreting an unbounded linear
projection as a realizable calibration. No minimum model separation is required
for a software check to pass.

Before recorded-data use, quantization, averaging, time association, receiver
derivative error and their dependence still need a consistent treatment.
Changing-motion support must be selected using receiver observations before
examining gyro or model residuals. Neither these controls nor a future scalar
ranking assigns a percentage of the original fit separation to gyroscopes.

The completed full-position comparison remains **53 globe / zero flat / zero
unresolved**. The separate IMU21 horizontal-only sensitivity result remains
unresolved. This work changes neither disposition.

[Complete matrix](README.md) · [All outcomes](controls.csv) ·
[Frozen scope](PLAN.md) · [Calibration-control design](../ilvis0-measurement-contribution/CALIBRATION_PLAN.md).
