# Analysis roadmap

## Where the project stands

<!-- current-status:start -->
**53 globe preferences, 0 flat preferences, 0 unresolved** among 53 preselected stretches.
See the [verified current status](CURRENT_STATUS.md) for coverage, background-field comparisons and the supporting result records. All selected comparisons have passed their required numerical checks.
<!-- current-status:end -->

The main model comparison is finished. The current priority is to check how
well the models predict measurements that were left out of the fit.

An **IMU (inertial measurement unit)** contains gyroscopes that measure turning
and accelerometers that measure specific force. The analysis combines those
records with receiver positions to reconstruct the aircraft's motion.

The 53 stretches favor globe geometry and the model with a specified background
rotation signal. These are completed model comparisons. Statistical confidence,
prediction accuracy and independence between recordings still need testing.

## The immediate obstacle

We need a reliable **error range** around each prediction: how far it could
move because calibration and measurement errors are uncertain.

The current calculation allows ranges that are too wide for useful tests over
a full stretch. That is a limitation of the calculation, not a measurement of
how badly the aircraft data fit.

The latest [192-box generated-data comparison](ilvis0-coupled-subdivision/INTERPRETATION.md)
passes every correctness check, but only four of six groups meet the fixed width
target. Both specified-field globe groups still miss it. No new aircraft fits ran.

Keeping calibration errors tied together and using smaller mounting-angle boxes
has helped only slightly. The [endpoint audit](ilvis0-coupled-subdivision/ENDPOINT_DIAGNOSIS.md)
points to conservative propagation allowances as the next target. The
[six-bound diagnostic](ilvis0-training-remainder-diagnostic/INTERPRETATION.md)
finds that smaller domains barely change the height allowance. Its original
comparison had a unit mismatch; the saved-only audit resolves that discrepancy
without rerunning any bounds. A [direction-preserving rotation component](ilvis0-directional-rotation/README.md)
now extends to calibrated force vectors and passes all [24 static controls](ilvis0-directional-force-controls/INTERPRETATION.md).
Their height ranges are substantially tighter. All
[24 native propagation controls](ilvis0-directional-native-controls/INTERPRETATION.md)
also pass under the original limits. The [prediction comparison](ilvis0-directional-prediction/INTERPRETATION.md)
then reached its time ceiling with 39 passing sectors. All four complete globe
groups retain their earlier widths; the fixed target still fails. The
[baseline audit](ilvis0-directional-prediction/BASELINE_DIAGNOSIS.md) shows that
the new static bound lost tighter training information. Next is direction-aware
dynamic propagation that preserves that information. A [componentwise value prototype](ilvis0-directional-dynamics/README.md)
now passes local controls for vector, matrix and scalar operations. A
[six-source preflight](ilvis0-source-norm-preflight/INTERPRETATION.md) now passes,
with vertical value intervals about 5.6–6.3% as wide as the actual baseline.
Reference-coefficient and remainder qualification still precede native integration.
The observations, physical bounds and acceptance target remain unchanged.

## Dependency-ordered backlog

Priority shows the order of work. “Software checked” means a calculation passed
known-answer tests; it does not mean the aircraft result has been independently
validated.

| ID | Priority | Status | Work |
|---|---|---|---|
| F01 | Foundation | Complete | [Group related recordings](analysis-provenance/README.md) so overlapping stretches are not counted as independent flights. |
| F02 | Foundation | Complete | [Reserve separate ESA flight groups](analysis-provenance/README.md) for a later independent test. |
| C01 | First | Complete | [Check the basic motion calculations](ilvis0-measurement-contribution/README.md). |
| C02 | First | Software checked | [Test which calibration changes can imitate a model difference](ilvis0-scalar-certificate-controls-20261019/INTERPRETATION.md). |
| C03 | First | Initial check complete | [Include measurement-error assumptions](ilvis0-channel-envelopes-20261019/INTERPRETATION.md) in the accelerometer-only checks. |
| C04 | First | Initial check complete | [Compare checks without gyroscopes](ilvis0-channel-history-v2-20261019/INTERPRETATION.md). These leave all models possible; they do not reconstruct a complete flight. |
| V01 | First | **In progress** | Keep prediction errors tied to one calibration. [Extreme-point diagnostic](ilvis0-calibration-map-diagnostic/INTERPRETATION.md); four of six groups pass the width target so far. |
| V02 | First | Waiting for V01 | Test predictions against measurements excluded from fitting, including height. [Earlier prediction evidence](ilvis0-saved-prediction-comparison/INTERPRETATION.md). |
| L01 | Next | Software checked | [Process long recordings](ilvis0-streaming-precision/INTERPRETATION.md) without excessive memory use. |
| E01 | Next | Receiver diagnostic complete; selection still open | [Position-based assessment](esa-position-assessment/INTERPRETATION.md) finds 96 robust quiet-trend checks. These are not eligible stretches; continuous motion and receiver-error validation remain. |
| E02 | Next | Waiting | Compare models on ESA development data, then test the frozen method on reserved flights. |
| G01 | Next | Complete as a descriptive check | [Compare raw gyro trends with geographic predictions](ilvis0-gyro-companion-v2/INTERPRETATION.md) across all 53 stretches. |
| U01 | Next | Development dataset ready | [Assemble the evidence for publication](PAPER_DATASET.md). Final prediction and uncertainty results are still needed. |
| U02 | Next | Waiting | Establish statistical confidence while accounting for related recordings and the two-stage model decision. |
| R01 | Later | Not started | [Estimate the background rotation vector freely](ROTATION_FIELD.md), rather than supplying its rate. |
| R02 | Later | Waiting for R01 | Test whether the measured rate can distinguish sidereal from solar timing. |
| S01 | Later | Deferred | Develop Wuhan-data analysis and the separate [stationary participant experiment](STATIONARY.md). |
| D01 | Supporting | Ongoing | Seek more instrument documentation. This supports the work without stopping analysis under stated assumptions. |

## What happens after the current diagnostic

1. Improve the prediction method and test its error ranges.
2. Fit part of a recording, then predict the unused part. Check absolute error,
   not just which model does better.
3. Prepare and test the separate ESA archive, keeping its reserved flights untouched
   until the method is fixed.
4. Establish confidence at the flight-group level. Then pursue the free rotation
   rate and solar-versus-sidereal studies.

Completed studies remain unchanged. A failed check blocks the work that depends
on it; it does not restart earlier studies or create extra attempts.

[Plain-language next steps](NEXT_STEPS.md) ·
[Technical requirements and supporting evidence](ANALYSIS_DETAILS.md) ·
[Completed studies](STUDIES.md).
