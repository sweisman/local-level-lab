# What comes next

The globe with a specified angular field fits all 53 selected aircraft
stretches better than the two zero-field alternatives. Among the zero-field
fits alone, the disc has the lower cost on 18 stretches under both processing
assumptions. The 53 stretches belong to 27 conservative flight groups.

First, test both geometries with the same field and measure what changes when
gyroscope data are omitted or the assumed offset limit is widened. Then run a
small NASA pilot before advancing aircraft prediction uncertainty and ESA
development. The [technical milestones](ANALYSIS_ROADMAP.md#current-milestones-and-finish-line)
give the conditions for expanding the pilot and opening independent flights.

A [matched ESA development forecast](prediction-observed-development/ESA_400_120_MODEL_MATRIX_INTERPRETATION.md)
now has two complete three-model settings, both favoring globe, and two
unresolved settings. Aircraft prediction uncertainty remains unqualified;
the seven reserved flight groups remain closed.

An **IMU (inertial measurement unit)** records angular motion with gyroscopes
and specific force with accelerometers. Its gyroscope measurements are central
to this project. The separate primary GPS receiver supplies positions that
constrain the reconstructed flight.

[Current findings](CURRENT_STATUS.md) ·
[All 53 stretches](ilvis0-current-findings-20261015/STRETCHES.md) ·
[Detailed CSV](ilvis0-current-findings-20261015/stretch-analytics.csv)

## ESA development update

**Check that the two solvers agree.** On one new ESA window, both solvers
converged in all 16 pairs. Their predictions from equally good starting
points stayed within 0.265 mm. Accuracy against later GPS positions is a
separate check. [Solver comparison](mixed-tangent-hybrid/OBSERVED_DISPATCH_FRESH_RESULT.md)

**Check whether an earlier error repeats.** A correction learned from
an earlier forecast improved later height estimates in 15 of 20 NASA
recording groups. Horizontal estimates improved in three. A height-only
correction improved all seven additional groups tested. Their median
height error fell from 4.25 m to 1.97 m, with horizontal errors unchanged.
The next check is whether this carries over to the ESA development flight.
[Earlier-error test](prediction-group-transfer/ERROR_TRANSFER_RESULT.md) ·
[Height-only test](prediction-group-transfer/HEIGHT_TRANSFER_RESULT.md)

**Set limits on calibration error.** On the same ESA development flight,
two calibration changes that still fit the earlier GPS positions moved
the forecasts a combined 0.43 units toward each other. The forecasts
started 25.41 units apart. The current bounds still allow 53.66 units
of movement, so the next step is to tighten how they link the
calibration terms. [Calibration replay and bounds](prediction-observed-development/ESA_LINKED_PHYSICAL_REPLAY_RESULT.md)

**Test the turn allowance on steadier flight.** Four steady-course
controls on the same flight now have verified training inputs. The
comparison will test whether the turn allowance helps specifically
when its timing follows the aircraft's motion.

## The work in order

1. Qualify the matched field, gyro-offset and gyro-free controls.
2. Run a small matched NASA pilot and expand only if it can answer a stated open question.
3. Qualify aircraft prediction uncertainty and test the three remaining ESA development windows.
4. Freeze the decision procedure before opening any reserved independent group.

## Current method check

The [finite 48-case generated-aircraft study](bounded-calibration-prediction/INDEPENDENT_SEEDS_RESULT.md)
is complete. All 48 fits passed their numerical and withheld-position checks
under the frozen assumptions. This qualifies the method check, but two new
noise draws per condition cannot establish 95% uncertainty coverage. The next
method gate is the [paired bound-family study](prediction-paired-bound-family/README.md):
its [combined 24-recording result](prediction-paired-bound-family/RESULT.md)
passes the technical gate. All 48 fits pass numerical and physical prediction
screens, and both target intervals contain every later coordinate in this
small generated matrix.
The first [96-recording whole-period study](prediction-simultaneous-law-family/RESULT.md)
stopped before any numerical work because its worker could not import a package.
Those failures remain sealed. A [fresh cohort](prediction-simultaneous-law-family-v2/RESULT.md)
passed its worker preflight and closed all 96 tasks without repeating a sealed
result. Ninety-two produced paired forecasts, and every later coordinate was
inside both intervals on those 92 recordings. Four tasks stopped at the original
eight-hour time limit. They count as failures, giving a 9.28% upper failure
bound; the predefined 5% gate failed. This is a generated method check, not
proof of aircraft coverage. Independent observed-flight checking remains gated.

A [saved ESA forecast check](esa-prediction-error-scale/README.md) shows why
this step matters: receiver-reported centimetre precision is much smaller
than later errors in an IMU-based aircraft prediction. A
[companion audit](esa-prediction-error-scale/CORRELATION.md) finds that those
forecast errors persist strongly over time. For the best fitting candidate,
later RMS errors are roughly 84–178 times the residual RMS from the fitted
earlier period, depending on direction. Good earlier fit quality therefore
cannot supply a future error limit. Hundreds of successive receiver epochs
from one flight cannot be counted as hundreds of independent tests.
The separate [NASA development pilot](ilvis0-retrospective-prediction-pilot-v2/ERROR_STRUCTURE.md)
also shows large growth between fitted earlier residuals and later forecast
errors. Its saved one-second errors grow across each withheld period; the
median specified-field globe height RMS rises from 1.73 m in the first
quarter to 14.10 m in the last. This points to accumulated prediction error,
not a receiver-only precision problem.
The [earlier-only transfer check](prediction-rolling-origin/INTERPRETATION.md)
is complete. It compares an earlier forecast error with a later, equally long
forecast from the same recording. Eight of twelve repeated settings have
passing fits at both cuts. The north error ratio ranges from 0.44× to 4.09×,
while height behaves differently across the three recordings. Those results
do not calibrate a single multiplier for future uncertainty. The study
preserves all 48 starts and fourteen nonpassing fits; its frozen plan's
preparation notes describe the sequence before launch.
A software check now preserves the union of forecast intervals from competing
error assumptions when training cannot distinguish them. It prevents a
premature choice; it does not show that real aircraft errors fall inside.
The [four-group NASA transfer check](prediction-group-transfer/RESULT.md)
sealed all 16 planned fits. Three groups have scorable second-cut forecasts;
all three meet the fixed descriptive error reference and physical screen.
The fourth abstains after numerical fit failures. This does not establish
coverage or a confidence claim.
The [receiver-only forecast control](receiver-only-forecast-baseline/INTERPRETATION.md)
predicts the three original pilot withheld periods from earlier GPS positions
alone. A [stronger spherical-path control](receiver-only-geodesic-control/INTERPRETATION.md)
reduces its horizontal errors to 33–189 m. The available IMU forecasts remain
closer, most clearly on the northern recording where every matched comparison
finishes. Both are receiver-only motion baselines; neither isolates the gyro
channel or calibrates an Earth-model test.
The seven reserved ESA groups can test whether a frozen method works on a
different aircraft survey, but seven flights alone cannot establish a rare
failure rate. [The sample-size calculation](PREDICTION_ERROR_LAW_PLAN.md#what-the-available-flight-count-can-establish)
sets out that limit.

## What is already established

- The specified-field globe had the lowest cost in both cases on all 53 stretches.
  The original 12 and later 41 used different numerical checks. See the [verified ledger](CURRENT_STATUS.md).
- The [raw-gyro companion](ilvis0-gyro-companion-v2/INTERPRETATION.md)
  compares measured angular trends with geographic predictions.
- The original files, integer IMU increments, receiver streams, selection
  rules, failed attempts and calculation receipts are retained.
- The NASA archive informed development. The reserved ESA groups provide a
  separate opportunity to test a frozen method.

[Method](METHODOLOGY.md) · [Technical roadmap](ANALYSIS_ROADMAP.md) ·
[Study history and results](STUDIES.md) ·
[Reproducibility](REPRODUCIBILITY.md) ·
[Rotation-field proposal](ROTATION_FIELD.md)
