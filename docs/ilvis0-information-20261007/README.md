# Does numerical identifiability provide useful calibration?

An optimizer can recover an injected value exactly from noiseless data yet be unable
to estimate that value usefully from uncertain measurements. The previous
[duration and rotation controls](../ilvis0-excitation-20261007/README.md) also found
that a numerical rank changed when only the assumed GPS errors changed. This check
asks how much calibration information survives, without using rank as a pass rule.

It uses the same 18 analytic fixtures: 2, 20 and 60 seconds, steady orientation or
a one-second 0.1-degree pitch correction, under three fixed GPS-error assumptions.
The baseline has an artificial millimetre-scale covariance. The other two add
correlated horizontal/vertical errors of 1/3 metres and 10/30 metres, respectively,
plus offsets and drift. These are sensitivity assumptions, not measured accuracy.
Only the covariance changes between each set of three cases.

Eight quantities vary together: initial position, velocity and pitch; gyro bias and
gain; acceleration bias and gain; and the GPS/IMU time offset. Their declared fixture
bounds set the coordinate scales. Those bounds are not supported hardware limits.
Every case uses four central derivative steps—0.0005, 0.001, 0.002 and 0.004 of each
bound—with positive and negative perturbations. No step is selected after seeing
its result. Independent analytic positions check the unchanged predictor.

## How to read the diagnostic

The whitened Jacobian measures changes in the predicted GPS positions relative to
the assumed measurement errors. Its singular values describe joint parameter
directions. A singular value above one means a change of one normalized unit along
that direction produces a local response larger than one whitened noise unit.
This is a scale comparison, not a hypothesis test or an operational threshold.

For a smooth diagnostic, add an artificial unit reference penalty in the declared
bound coordinates. The data-resolution matrix is
`R = JᵀJ (I + JᵀJ)⁻¹`, calculated by SVD. Its diagonal describes how much the data
reduce each coordinate's unit reference variance while allowing the other
quantities to vary. The reported reference sensitivity is
`sqrt(diag((I + JᵀJ)⁻¹))`, expressed as a fraction of the declared bound and in
physical units. An entirely unobserved quantity retains sensitivity one. This
avoids falsely assigning a precise estimate to a null direction through a
pseudoinverse. The reference penalty is not a calibrated prior or a confidence
interval, and these values are not data-only marginal standard deviations.

The report preserves all four derivative calculations. It compares their resolution
matrices and flags operator changes above 0.02. That tolerance is a provisional
software diagnostic, never a scientific gate. Three times the largest inter-step
Jacobian difference supplies a numerical noise proxy; adding and subtracting it
from each singular value shows whether the unit-information classification is
sensitive to that proxy. This is not a rigorous derivative-error bound. Agreement
across the tested steps cannot establish convergence at every smaller step or
validate the physical instrument model.

## Reproduction and scope

All 18 independent trajectory checks pass. All 72 derivative calculations are
preserved, with no resolution-stability failures. The largest resolution-matrix
change is 0.000510, below the declared 0.02 diagnostic tolerance. All 384
per-parameter comparisons between successive GPS-error assumptions obey the
expected information decrease, allowing a numerical tolerance of 1e-9.
Twenty focused tests pass: twelve new diagnostic/persistence tests and eight
preceding analytic fixture tests. The run used 18 starts and 1,170 predictions;
there were no optimizer calls. Each task's interruption allowance was two starts.

The correlated-error cases retain one joint direction above the unit-information
scale at two seconds; two or three at twenty seconds; and three at sixty seconds.
Those directions can mix several parameters and do not establish separate
calibration of each one. The millimetre toy cases have four, seven and seven/eight,
respectively. In the sixty-second toy pitch case, eight singular values exceed one,
but the observed derivative-noise proxy leaves seven/eight possible. That boundary
ambiguity is retained despite the small change in the smooth resolution diagnostic.

The table gives the largest reference sensitivity across the four steps, as a
fraction of the declared bound. Values near one mean nearly all of the artificial
reference uncertainty remains. These are neither measured errors nor data-only
confidence intervals.

| Duration and motion | GPS-error assumption | Gyro bias remaining fraction | Gyro gain remaining fraction |
|---|---|---:|---:|
| 20 s, brief pitch | Millimetre toy | 0.0614 | 0.9806 |
| 60 s, brief pitch | Millimetre toy | 0.00132 | 0.6842 |
| 20 s, brief pitch | Correlated 1/3 m | 0.9994 | >0.999999 |
| 60 s, brief pitch | Correlated 1/3 m | 0.8741 | >0.999999 |
| 20 s, brief pitch | Correlated 10/30 m | 0.99993 | >0.999999 |
| 60 s, brief pitch | Correlated 10/30 m | 0.9910 | >0.999999 |

Without rotation, gyro gain is exactly unobserved and its remaining reference
fraction stays one, up to floating-point roundoff. Longer duration helps gyro bias;
the tiny pitch correction still supplies almost no gyro-gain calibration under the
correlated assumptions. Reference regularization also limits nuisance variation,
so its smaller sensitivities must not replace the earlier unbounded joint-precision
results. The main limitation here is useful information under the assumed errors,
rather than an unstable derivative calculation. No covariance or instrument bound
was selected or calibrated by this result.

The [parameter inventory](inventory.csv) retains every parameter and step. The
completed evidence includes hashes of inputs and source snapshots, the numerical
environment, per-task receipts, an interruption journal and a compressed full
report. `export_inventory.py` verifies those records and packages them without
rerunning predictions. A completed worker must not be resumed. Revised source or
assumptions require a new separately named freeze.

No original was rescanned or deleted. All 232 stored originals remain. No archived
IMU fit, Earth-model fit, flight campaign or eligibility change ran. The estimator
and earlier evidence stay frozen. Instrument-specific processing, mounting,
calibration and clock support are still required by the empirical fitting gate;
software fixtures cannot supply them. See the
[instrument evidence matrix](../ilvis0-excitation-20261007/INSTRUMENT_EVIDENCE.md).
