# Account for errors that accumulate over time

**The shared calculation passes 54 source-bound software checks.** Its
eight-state storage test handles 64,080 generated observation times with
59.2 MiB of stored operator arrays.
Small problems agree with independent dense calculations, including all 27
parameter columns, changing time steps and correlations between axes.

A small gyro error can tilt the reconstructed direction of gravity. The
resulting position error grows and remains correlated across later times.
This component provides a practical way to calculate with a supplied error
law while preserving that correlation. It also supports continuous blocks,
so processing a recording in sections does not reset its error history.

Small constant-level examples with a perfect initial state and declared white
gyro/accelerometer noise match the analytic covariance. The long case checks
storage and execution without constructing a dense reference. The aircraft
error law and uncertainty from fitted calibration parameters still need
establishing. Existing flight fits, accuracy limits and protected recordings
are unchanged.

The [current qualification receipt](joint-qualification/evidence-receipt.json)
binds exact source versions, environment and passing tests. The earlier
[26-check](qualification/evidence-receipt.json) and
[32-check](forecast-qualification/evidence-receipt.json) and
[46-check](ou-qualification/evidence-receipt.json) snapshots remain
preserved. Shared archive storage retains the versions without copying a
library tree. The existing receiver-error operator is unchanged.

Conditional future means and per-epoch uncertainty now match independent dense
Gaussian conditioning at four training cutoffs. The calculation uses only an
earlier-error checkpoint. Unknown future errors remain random; their effects
are retained rather than treating earlier withheld positions as known.

A thirteen-state example now also includes slowly changing gyro and
accelerometer bias. It agrees with independent covariance integrals and the
noise generator's separate endpoint/integral formulas, including the declared
stress amplitudes at 1/300, 1 and 400 seconds. These are generated software
checks with fixed parameters.

The joint-noise mode also preserves a query and endpoint driven by the same
increment. Its covariance and earlier-only conditional predictions match dense
controls; replacing the shared noise with independent errors gives a different
answer. The original after-transition mode retains its meaning.

The receiver-error extension passes another **15 source-bound checks**. It
carries offsets, drift and up to two persistent error components across the
training/prediction boundary, preserving changing cross-axis transformations.
Small generated examples agree with independent dense calculations and
earlier-only predictions. The largest checked state has 27 coordinates.
All 24 [publication artifact hashes](receiver-qualification/evidence-receipt.json)
are verified; this adds no flight fitting or instrument-noise estimate.

The [native calculation](../native-noise-linearization/README.md) now also
passes 38 complete-history checks, following its 18 single-step checks.
Their [combined path](../native-noise-linearization/COMBINED_PLAN.md) passes
twelve more native checks, including every active calibration column and
earlier-only conditional prediction.

The [linear calibration extension](CALIBRATION_PLAN.md) passes **15 checks**.
It includes uncertainty from learning calibration on earlier observations.
It returns no finite prediction covariance when an unknown calibration
direction could change the forecast. Dense reference calculations agree for
all 27 columns. Its 23 [artifact hashes](calibration-qualification/evidence-receipt.json)
are verified. This assumes a linear mean and unrestricted calibration;
native nonlinear fits and parameters at bounds still require qualification.

The [ESA rate-point law](POINT_PLAN.md) passes **15 checks** against an
independent calculation from sample errors. Neighboring intervals share an
endpoint sample, so their errors remain correlated after conversion to
increments. Point variance and continuous noise PSD remain distinct inputs.
All 23 [artifact hashes](point-qualification/evidence-receipt.json) are verified.
The [native adapter](../native-noise-linearization/README.md) now passes 65
checks within a 182-check source-bound qualification. It retains the larger
rate-point state and all 33 states in the full receiver combination. Nominal
positions, covariance and calibration columns agree with independent controls.
The [training-only native fitting adapter](training-adapter-qualification/README.md)
now passes 56 checks across all three models and both input formats. It preserves
every calibration column and the earlier-only boundary without a dense whole-record
covariance. Active calibration bounds and nonlinear coverage remain to qualify.

The [prepaid-work extension](prepaid-native-qualification/README.md) passes 112
bookkeeping checks. Long calculations can reserve a bounded block of native
calls once, retaining the full charge after interruption and enforcing each
attempt locally. This removes per-packet durable transactions without changing
the numerical calculations. No measured speedup or prediction claim is made.

The [sampled-rate error generator](rate-point-input-qualification/README.md)
passes 54 checks, including an independent covariance calculation and exact
earlier-prefix reproducibility. This supplies realistic error sharing for
[the next nonlinear fitting controls](NONLINEAR_PLAN.md); it does not estimate
the actual instrument's noise.

The [complete short native protocol](short-native-protocol-qualification/README.md)
now passes 128 software checks. All twelve two-second examples return forecasts
within the physical screen, while retaining numerical nonconvergence and
unidentified calibration. This qualifies the connected interface, including
separate receiver-reading and physical-position targets. Longer noisy fitting
and uncertainty coverage remain to test.

The [two-minute study](../structured-noisy-training/README.md) now returns all
24 forecasts within the physical limits, with 20 numerical passes. All fits
reach calibration bounds, so the uncertainty gate remains open. This is a
different duration from the earlier twenty-minute failed controls; it cannot
establish that the revised weighting fixes that longer prediction problem.

[Frozen software plan](PLAN.md) ·
[Conditional forecast plan](FORECAST_PLAN.md) ·
[Changing-bias plan](OU_PLAN.md) ·
[Shared query/endpoint noise plan](JOINT_PLAN.md) ·
[Persistent receiver errors](RECEIVER_PLAN.md) ·
[Estimated calibration uncertainty](CALIBRATION_PLAN.md) ·
[Shared rate-point errors](POINT_PLAN.md) ·
[Why gyro error accumulates](../esa-noisy-prediction/ERROR_BUDGET.md) ·
[Prediction error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
