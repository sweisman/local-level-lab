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

The [saved prediction check](ilvis0-saved-prediction-comparison/INTERPRETATION.md)
already records about 2.4 m later horizontal RMS for the specified-field globe,
versus 143–255 m for the alternatives, on one recording. The next objective is
to test repetition across different conservative flight groups and IMU types.
These remain retrospective development tests; reserved ESA groups stay protected.

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
| V01 | First | **Forecast adapter checked; full pipeline next** | The [revised protocol](PREDICTION_VALIDATION.md) has 29 passing forecast checks. Next qualify initialization, training-only fitting and prediction together. Keep matched bounds and assumptions; global interval certification is separate. |
| V02 | First | Pilot preparation; fits wait for revised V01 | Freeze a metadata-selected pilot, splits, starts, error scoring and finite limits; then test unused positions, including height. [Earlier prediction evidence](ilvis0-saved-prediction-comparison/INTERPRETATION.md). |
| L01 | Next | Long-prefix reuse qualified; larger-scale work remains | [All six 96,000-packet histories](ilvis0-native-prefix-format-recovery/README.md) preserve complete reports and 51 columns. Dense query counts and longer ESA histories still need their own timing, memory and prediction checks. |
| E01 | Next | Receiver diagnostic complete; adapter capability and selection open | [Position-based assessment](esa-position-assessment/INTERPRETATION.md) finds 96 quiet trends. [Sampling alone cannot certify continuous quiet motion](ESA_MOTION.md); justify a motion bound or qualify complete maneuver handling, then freeze selection and receiver-error rules. |
| E02 | Next | Waiting | Compare models on ESA development data, then test the frozen method on reserved flights. |
| G01 | Next | Complete as a descriptive check | [Compare raw gyro trends with geographic predictions](ilvis0-gyro-companion-v2/INTERPRETATION.md) across all 53 stretches. |
| U01 | Next | Development dataset ready | [Assemble the evidence for publication](PAPER_DATASET.md). Final prediction and uncertainty results are still needed. |
| U02 | Next | Waiting | Establish statistical confidence while accounting for related recordings and the two-stage model decision. |
| R01 | Later | Not started | [Estimate the background rotation vector freely](ROTATION_FIELD.md), rather than supplying its rate. |
| R02 | Later | Waiting for R01 | Test whether the measured rate can distinguish sidereal from solar timing. |
| S01 | Later | Deferred | Develop Wuhan-data analysis and the separate [stationary participant experiment](STATIONARY.md). |
| D01 | Supporting | Ongoing | Seek more instrument documentation. This supports the work without stopping analysis under stated assumptions. |

## What happens after the current diagnostic

1. Qualify the training-only fitting and prediction pipeline on known-answer controls.
2. Run the preselected archival pilot. Check all position components and start-to-start
   sensitivity; do not treat these as calibrated confidence intervals.
3. Prepare and test the separate ESA archive, keeping its reserved flights untouched
   until the method is fixed.
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
