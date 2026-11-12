# What comes next

The main airborne analysis is numerically complete. **All 53 selected stretches
fit globe geometry better than the tested flat-disc model.** They also favor
the model with a specified background angular field over the zero-field
model. These are numerical preferences, not a calibrated confidence claim or
53 independent flights. The data do not identify the cause of the field.

An **IMU (inertial measurement unit)** records angular motion with gyroscopes
and specific force with accelerometers. Its gyroscope measurements are central
to this project. The separate primary GPS receiver supplies positions that
constrain the reconstructed flight.

[Current findings](CURRENT_STATUS.md) ·
[All 53 stretches](ilvis0-current-findings-20261015/STRETCHES.md) ·
[Detailed CSV](ilvis0-current-findings-20261015/stretch-analytics.csv)

## The work in order

| Step | Current status | What must happen next |
|---|---|---|
| **1. Test predictions on unused measurements** | The 96-recording generated whole-period check finished, but four recordings stopped at its time limit, so its 5% coverage gate failed. The NASA retrospective pilot and one ESA development recording have usable forecasts; their absolute aircraft error is not yet calibrated. | Diagnose the four time-limit failures without rerunning them. Qualify a separate finite method check before using independent flights. |
| **2. Isolate what the gyroscopes add** | Checks using accelerometer magnitude alone leave all tested models possible. Removing height from one fit still favors globe but can produce physically impossible altitudes. | Make a complete matched comparison with and without the gyro channel, retaining the same real observations and explicit orientation uncertainty. |
| **3. Repeat with a different archive** | One ESA development recording has been parsed and tested. Seven separate flight groups remain reserved. | Freeze interval selection, error assumptions and decision rules before opening those reserved groups for confirmation. |
| **4. Establish independent evidence and confidence** | The 53 stretches belong to 27 conservative flight groups. A separate generated-data calibration and validation passed under its simulated conditions. | Account for shared flights and instruments, fit the observed error structure, and calibrate the complete shape-then-field decision. |
| **5. Measure the angular field freely** | The present model comparison tests a specified field against zero; it does not freely estimate the field's rate or cause. | After the prediction and uncertainty work, fit field direction and magnitude across flights. Test solar versus sidereal rate only if the resulting precision supports it. |

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

- All 53 selected main comparisons passed their numerical stopping checks.
  None preferred the tested flat disc.
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
