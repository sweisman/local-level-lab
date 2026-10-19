# Studies and what each added

**All 53 selected airborne stretches favor globe in the complete full-position
comparison.** The studies below explain how that result was obtained and what
has been checked since. Repeated fits and overlapping recorders do not create
additional independent flights.

An **IMU (inertial measurement unit)** contains gyroscopes and accelerometers.
The gyroscope record measures turning; receiver positions and acceleration
constrain the reconstructed track.

[Verified current findings](CURRENT_STATUS.md) ·
[All 53 stretches](ilvis0-current-findings-20261015/STRETCHES.md) ·
[Comprehensive CSV](ilvis0-current-findings-20261015/stretch-analytics.csv) ·
[Next analyses](NEXT_STEPS.md).

## From recordings to the complete comparison

| Study or stage | What it added |
|---|---|
| [Reference inspection](research-next-stage-20261006/airborne-sample-ilvis0/README.md) and [physical decoding](ilvis0-physical-validation-20261007/README.md) | Recovered intact packet framing, raw angle/velocity increments, units, signs and embedded receiver output. |
| [Other IMU configurations](ilvis0-imu21-assessment-20261007/README.md) and [IMU6 checks](ilvis0-imu6-cross-date-20261007/README.md) | Kept instrument-specific conversion hypotheses separate rather than assuming one format for every file. |
| [Recording screening](ilvis0-retention-84-20261007/README.md) and [motion screening](ilvis0-motion-61-20261007/README.md) | Recorded keep, reject and unsupported outcomes; 232 originals were retained. |
| [Receiver extraction](ilvis0-observation-20261007/README.md) and [GPS checks](ilvis0-gnss-v2-20261007/README.md) | Separated raw inertial observations and primary-receiver positions from the fused navigation solution. |
| [Frozen eligibility inventory](ilvis0-highspeed-segments-20261008/ELIGIBILITY.md) | Selected 53 complete, steady stretches lasting at least four minutes at 700 km/h or faster, before model fitting. |
| [First selected-stretch run](ilvis0-highspeed-segments-20261008/FINDINGS.md) | Completed twelve globe preferences and left 41 numerical comparisons unfinished. |
| [Numerical recovery and final review](ilvis0-last-review-20261018/README.md) | Resolved all 41 using separately checked methods while preserving the observations, physical assumptions and earlier failures. |
| [Combined findings](CURRENT_STATUS.md) | Count each stretch once: **53 globe, zero flat, zero unresolved**; all also prefer the specified background field over zero. |

The [detailed study history](STUDY_HISTORY.md) preserves every intermediate
recovery stage and the approaches that did not qualify.

## What drives the separation?

| Check | What it added or left open |
|---|---|
| [Raw gyroscope overview](ilvis0-gyro-overview/README.md) | Visualizes the same-sign accumulated pitch motion in all selected stretches; it is not a separate curvature test. |
| [Residual and calibration audit](ilvis0-calibration-audit-20261010/README.md) | Found a large in-sample fitting-error gap on the original twelve stretches, alongside frequent calibration parameters at their bounds. |
| [Refitted clock comparison](ilvis0-clock-trial-20261010/README.md) | All six fits completed and preserved globe/field preferences after changing the timing convention and reoptimizing. |
| [Calibration grid](ilvis0-z-profile-audit-20261011/README.md) and [replication audit](ilvis0-z-followup-audit-20261012/README.md) | Tested gain, bias and processing alternatives; preserved complete comparisons and unresolved grid nodes separately. |
| [Saved coordinate-subset scores](ilvis0-receiver-projection-20261018/README.md) | All 36 horizontal-only processing-case comparisons favor globe at existing parameters; no refit or channel isolation was performed. |
| [First horizontal-only refits](ilvis0-horizontal-repeat-audit-20261019/INTERPRETATION.md) | One of two stretches passed all repeats and favored globe; the other remained unresolved. Unscored height paths were implausible. |
| [Matched timing search](ilvis0-horizontal-multistart-20261019/INTERPRETATION.md) | Passed 37/38 individual fits and both controls, but only 2/6 selected repeat comparisons; the IMU21 sensitivity result remains unresolved. |
| [Channel-removal controls](ilvis0-measurement-contribution/CHANNEL_CONTROLS.md) | Passed 25 software checks and defined an acceleration-only diagnostic without fused attitude; recorded-data qualification remains ahead. |
| [Independent trajectory-force controls](ilvis0-channel-trajectory-controls-20261019/INTERPRETATION.md) | All 18 mathematical controls passed; exact-trajectory acceleration comparisons can separate some generated cases without gyroscopes. |
| [Receiver-derivative checks](ilvis0-channel-trajectory-controls-20261019/DERIVATIVES.md) | Passed 22 unit checks for derivatives, joint covariance, overlapping-window dependence and covariance symmetry. |
| [Approximation and averaging controls](ilvis0-channel-error-budget-20261019/INTERPRETATION.md) | Completed 46 implementation checks and preserved 27/108 approximation-screen failures; quantified polynomial bias, nonlinear magnitude bias and aggregation effects. |
| [Acceleration calibration ambiguity](ilvis0-measurement-contribution/CALIBRATION.md) | Nine known-answer checks show that small constant gain changes erase scalar model separation on a constructed straight leg; changing geometry needs a full-calibration check. |
| [Changing-motion calibration matrix](ilvis0-scalar-calibration-controls-20261019/INTERPRETATION.md) | All 72 local controls pass with seven calibration directions. Changing motion retains local differences, while wrong-model linear corrections exceed bounds; bounded nonlinear checks remain. |

On the original twelve completed comparisons, median horizontal in-sample errors
were about **0.068 m** for specified-field globe, **29.5 m** for zero-field globe
and **47.1 m** for flat. These figures are not prediction accuracy on unused data,
and they are not summaries of all 53 stretches.

The [measurement-contribution overview](ilvis0-measurement-contribution/README.md)
connects these checks and explains why removing a scored coordinate is different
from removing a sensor observation.

## Prediction, uncertainty and independence

| Check | What it added or left open |
|---|---|
| [Individual-epoch residuals](ilvis0-residual-diagnostic-20261010/README.md) and [covariance audit](ilvis0-residual-covariance-20261012/README.md) | Exposed temporal correlation and clock sensitivity; small fitting errors alone do not calibrate confidence. |
| [Reserved-time prediction trial](ilvis0-prediction-trial-20261011/RESULTS.md) | Five of six fits completed; the combined prediction comparison remained unfinished. |
| [Training/prediction covariance trial](ilvis0-prediction-covariance-20261012/RESULTS.md) | Ten of twelve fits completed; it did not establish calibrated predictive coverage. |
| [Shared-flight diagnosis](ilvis0-shared-leg-diagnosis-20261014/README.md) | Distinguished simultaneous-recorder agreement from numerical stopping differences and identified overlapping observations. |

These studies provide development evidence. A calibrated significance level,
absolute predictive adequacy and independent-replication count remain open.

## Separate sources and experiments

| Work | Present scope |
|---|---|
| [ESA and Wuhan data](external-imu-data/README.md) | Longer raw recordings have been inspected, but neither source has entered the Earth-model comparison. |
| [Free rotation-field study](ROTATION_FIELD.md) | Planned measurement of field direction and magnitude, followed by a solar/sidereal precision assessment; no free-rate result is claimed. |
| [Stationary crowdsourcing](STATIONARY.md) | A developing consumer-IMU reversal experiment; its diagnostic does not issue scientific detections. |

Historical simulated-flight campaigns and software trials remain available in
the [detailed history](STUDY_HISTORY.md). Their thresholds do not transfer to
these observations or to the stationary experiment.
