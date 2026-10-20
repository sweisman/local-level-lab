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

The latest comparison passes all 48 correctness checks and the width target
in four of six groups. Both specified-field globe groups still miss it. Stronger
matrix relationships barely helped. Next we will check whether the extreme error
combinations allowed by the calculation can come from one physical calibration.
No new aircraft fits ran.
[Latest result](ilvis0-product-prediction/INTERPRETATION.md).

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
| V01 | First | **In progress** | Make prediction error ranges useful over full recordings. [Four of six groups](ilvis0-product-prediction/INTERPRETATION.md) pass the current width target. |
| V02 | First | Waiting for V01 | Test predictions against measurements excluded from fitting, including height. [Earlier prediction evidence](ilvis0-saved-prediction-comparison/INTERPRETATION.md). |
| L01 | Next | Software checked | [Process long recordings](ilvis0-streaming-precision/INTERPRETATION.md) without excessive memory use. |
| E01 | Next | More checks needed | [Prepare the ESA data](esa-development-selection/README.md). No interval yet passes its current selection rules. |
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
