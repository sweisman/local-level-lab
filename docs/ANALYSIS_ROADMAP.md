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

## Next: test predictions on unused measurements

The [revised prediction protocol](PREDICTION_VALIDATION.md) separates a practical
prediction comparison from formal uncertainty certification. First qualify the
training-only fitting and prediction pipeline on known-answer controls. Then fit
earlier observations in a small, metadata-selected archival pilot and score
later positions without using them to adjust the answer.

Preserve the original physical bounds and compare all three candidates under
matched assumptions. Use predeclared starts, choose primaries by training cost
only, and report every failure. Show horizontal and height errors together.
Differences between repeated predictions are sensitivity evidence, not confidence
intervals. Actual error-law assessment and calibrated significance remain open.

The [completed prediction pilot](ilvis0-retrospective-prediction-pilot-v2/INTERPRETATION.md)
fully compares one recording across both clocks and both processing assumptions:
later horizontal RMS is 0.84–1.13 m for specified-field globe, about 496 m for
zero-field globe and 793 m for disc. Two other recordings retain numerical or
accuracy failures. Broader validation remains open. These are retrospective
development tests; reserved ESA groups stay protected.

Global interval certification is now a separate research track. Its earlier
bounds and counterexamples remain published, with unchanged failure labels and
width targets. The [completed training-bound study](ilvis0-dense-physical-bounds/INTERPRETATION.md)
preserved 348 reports, but none of its six cases qualified. No further bound
expansion precedes the revised prediction sequence.

[Revised method and safeguards](PREDICTION_VALIDATION.md) ·
[Error assumptions](PREDICTION_ERROR_ASSUMPTIONS.md) · [Study history](STUDIES.md).

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
| V01 | First | **24/24 matched controls qualified** | The [revised comparison](ilvis0-near-zero-forecast-controls/README.md) passes every generated case with unchanged physics, bounds and total call limits. It charged 2,976 native calculations. The original 3/24 result remains preserved. This qualifies the tested software procedure, not aircraft adequacy or statistical significance. |
| V02 | First | **Pilot complete: one recording passes the full prediction comparison** | The [verified pilot](ilvis0-retrospective-prediction-pilot-v2/INTERPRETATION.md) returns all 72 fits; 49 pass numerical checks. All four matched settings complete on the northern recording, with 0.84–1.13 m later horizontal RMS for specified-field globe versus hundreds of metres for the alternatives. The other two recordings retain numerical or accuracy failures. |
| L01 | Next | Accumulated-error covariance and conditioning software checked | The [new shared component](integrated-noise-covariance/README.md) passes 54 checks, including earlier-only prediction, slowly changing bias and shared query/endpoint noise. Its eight-state storage case handles 64,080 generated epochs with 59.2 MiB of arrays. The [faster arithmetic prototype](mixed-tangent-long-controls/README.md) remains unqualified because its derivatives miss the fixed tolerance. |
| E01 | Next | **Software, inventory and interval preparation complete** | The [72 adapter cases](esa-geographic-rate-controls/README.md), [24 known-correction cases](esa-observation-controls/README.md) and [24 training-only fits](esa-training-forecast-controls/README.md) pass. Two [working receiver-error cases](ESA_ERROR_POLICY.md) pass 76 checks. The [frozen full-motion inventory](esa-development-selection-v2/README.md) admits two runs totaling 393.4 minutes after 154 software checks. The [first twenty-minute interval](esa-development-pilot-preparation/README.md) is prepared and verified. All 48 matched weighted controls pass; actual error coverage remains uncalibrated. |
| E02 | Next | **Pilot complete: three adequate matched comparisons** | The [verified revision](esa-observed-wide-pilot/INTERPRETATION.md) supplies 22 qualified forecasts; three complete settings favor globe plus the specified field, with about 15 m later 3D RMS versus kilometres for the alternatives. Two disc starts reach the runtime ceiling. Error assumptions and broader validation remain open; seven confirmation groups stay protected. |
| G01 | Next | Complete as a descriptive check | [Compare raw gyro trends with geographic predictions](ilvis0-gyro-companion-v2/INTERPRETATION.md) across all 53 stretches. |
| U01 | Next | Development dataset ready | [Assemble the evidence for publication](PAPER_DATASET.md). Final prediction and uncertainty results are still needed. |
| U02 | Next | **Error adapter qualified; noisy prediction still open** | The [completed noisy test](esa-noisy-prediction/INTERPRETATION.md) returns 24 numerical passes and zero accuracy passes: horizontal RMS is 83.6–88.6 m against 10 m. Following the [182 component checks](native-noise-linearization/README.md), the [training-only adapter](integrated-noise-covariance/training-adapter-qualification/README.md) passes 56 checks. Nonlinear fits, active bounds and coverage remain; broader observed fitting stays gated. |
| R01 | Later | Not started | [Estimate the background rotation vector freely](ROTATION_FIELD.md), rather than supplying its rate. |
| R02 | Later | Waiting for R01 | Test whether the measured rate can distinguish sidereal from solar timing. |
| S01 | Later | Deferred | Develop Wuhan-data analysis and the separate [stationary participant experiment](STATIONARY.md). |
| D01 | Supporting | Ongoing | Seek more instrument documentation. This supports the work without stopping analysis under stated assumptions. |

## What happens after the current diagnostic

1. Preserve the qualified software controls and completed archival pilot, including
   its numerical and accuracy failures. Broader prediction validation remains open;
   ranges across starts are not calibrated confidence intervals.
2. Preserve the completed ESA comparisons and their failures. The
   [height-gravity revision](esa-observed-height-pilot/README.md) improves the
   matched prediction and completes one adequate three-model setting. Diagnose
   its stopping failures using the [completed fit-free resolution probe](esa-stopping-resolution/README.md).
   The [precision comparison](esa-precision-diagnostic/README.md) completes all
   24 cases: extended integration precision brings all eight field-globe cost
   changes below the existing limit. This diagnoses precision sensitivity at the
   saved points; it does not qualify a revised solver or accept failed fits.
   All [48 long known-motion controls](esa-wide-tangent-controls/README.md) now pass.
   The [matched training study](esa-wide-training-controls/README.md) now
   qualifies all 24 cases, using 268 calls in 113.96 minutes. The
   [observed precision revision](esa-observed-wide-pilot/INTERPRETATION.md) now
   completes three adequate matched comparisons after 56 source-bound checks.
   It preserves all 24 outcomes: 22 numerical passes and two deadline-limited
   starts. The [saved-error check](esa-error-structure/INTERPRETATION.md) now
   verifies all 22 curves without refitting. Errors and their changes remain
   strongly correlated; a receiver-only error assumption is not a complete
   prediction-error law. The [known-noise study](esa-noisy-prediction/README.md)
   completes all 24 fits numerically, but none meets the unchanged physical
   accuracy screen. Later horizontal RMS is 83.6–88.6 m. The
   [verified interpretation](esa-noisy-prediction/INTERPRETATION.md) preserves
   all failures; broader prediction tests remain gated on the revised error model.
   The [training-only rate diagnostic](esa-training-rate-variation/README.md)
   now verifies six-channel variation over 13.33 minutes without fitting. Its
   dependence on sample spacing means that aircraft motion and processing must
   remain distinct from a white sensor-noise assumption. No stress-test setting
   or accuracy limit is changed by this descriptive check.
   The [checked error-budget example](esa-noisy-prediction/ERROR_BUDGET.md)
   also shows why gyro uncertainty accumulates into correlated position errors.
   A revised stochastic prediction-error model needs its own qualification;
   choosing a larger error allowance merely to pass is not a substitute.
   The [shared covariance component](integrated-noise-covariance/README.md)
   now passes 54 software checks, including conditioning across the training
   boundary, stationary changing bias and shared query/endpoint errors. The
   [Native state/input derivatives](native-noise-linearization/README.md) now
   pass 18 source-bound checks across all twelve candidate/processing/gravity
   combinations. Their [complete-history extension](native-noise-linearization/HISTORY_PLAN.md)
   now passes 38 source-bound checks: all twelve longer generated cases preserve
   the nominal positions, and short histories agree with independent nonlinear
   noise perturbations. A separate [receiver extension](integrated-noise-covariance/RECEIVER_PLAN.md)
   passes 15 source-bound checks for offsets, drift, persistent errors and
   earlier-only prediction. Their [combined path](native-noise-linearization/COMBINED_PLAN.md)
   passes twelve native checks with every active calibration column retained.
   The [linear calibration extension](integrated-noise-covariance/CALIBRATION_PLAN.md)
   passes 15 checks and abstains when an unknown calibration direction changes
   the forecast. The separate [ESA rate-point law](integrated-noise-covariance/POINT_PLAN.md)
   passes 15 checks, preserving shared samples between neighboring intervals.
   Its [native adapter](native-noise-linearization/README.md) now passes 65
   checks within a 182-check source-bound suite, retaining both input laws and
   the full 33-state receiver combination. The
   [training-only native adapter](integrated-noise-covariance/training-adapter-qualification/README.md)
   now passes 56 checks. A separate [112-check accounting gate](integrated-noise-covariance/prepaid-native-qualification/README.md)
   permits bounded native blocks without per-packet durable transactions.
   The [sampled-rate error generator](integrated-noise-covariance/rate-point-input-qualification/README.md)
   also passes 54 checks. The [short native protocol](integrated-noise-covariance/short-native-protocol-qualification/README.md)
   now passes 128 software checks. Its two-second cases retain numerical
   nonconvergence and unidentified calibration; they do not qualify longer
   prediction. The [two-minute noisy study](structured-noisy-training/README.md)
   is now running 24 starts with more earlier observations and the full fitting
   allowance. Nonlinear coverage and active bounds remain open before new aircraft fits.
   Accuracy limits, input selection and calibration bounds remain unchanged.
3. Test broader predictive accuracy before opening the reserved ESA flight groups.
   The [fixed metadata plan](esa-broader-development/README.md) selects the first
   and last twenty minutes of each eligible development run: four ranges, one
   already analyzed and three additional candidates. They share one group and
   require separate preparation and fitting gates. Confirmation groups remain
   untouched until selection, method and decision rules are fixed.
4. Establish confidence at the flight-group level. Then pursue the free rotation
   rate and solar-versus-sidereal studies.

Completed studies remain unchanged. A failed check blocks the work that depends
on it; it does not restart earlier studies or create extra attempts.

Study orchestration and evidence storage use the [shared reproducibility
interface](REPRODUCIBILITY.md). Historical code and evidence retain their original
bytes inside verified archives; storage changes do not alter qualification.

[Plain-language next steps](NEXT_STEPS.md) ·
[Technical requirements and supporting evidence](ANALYSIS_DETAILS.md) ·
[Completed studies](STUDIES.md).
