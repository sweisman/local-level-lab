# What comes next

The fitted comparison is complete for the 53 selected NASA stretches. The globe with the specified background field had the lowest fitted cost in every stretch under both processing assumptions. Later GPS positions have also been predicted successfully on several development flights. The next milestone is a test on independent flights with a justified error model. [Verified findings](CURRENT_STATUS.md)

## Before confirmation

1. **Measure errors that several instruments could share.** Three GPS solutions on the ESA development flight share one antenna. A fixed error in its placement would need to be at least 40 cm to close the tested score gap under the gyro assumptions. The actual placement error and other shared aircraft errors remain open. In the NASA forecasts, shared GPS error could spoil prediction accuracy well before it changed which model fit best. [ESA antenna offset check](prediction-observed-development/ESA_CARRIER_LEVER_SENSITIVITY_RESULT.md) · [NASA forecast check](ilvis0-measurement-contribution/MATCHED_COMMON_ERROR_MARGIN_RESULT.md)
2. **Freeze the forecast and decision rules.** Decide how much of a flight to use for calibration, which positions to withhold, what counts as accurate enough, and how to handle failed or inconclusive comparisons. Test the complete rule on relevant known-answer cases before using it on the reserved flights. [Prediction method](PREDICTION_VALIDATION.md) · [Flight-group decision rule](FLIGHT_GROUP_DECISION.md)
3. **Run the frozen comparison on the reserved ESA groups.** All seven have at least one 20-minute slice with verified timing. The timing check established continuity and left the comparison outcomes unopened. Use matched geometry tests, check absolute prediction error, and report missing or inconclusive groups. [Receiver screen](external-imu-data/ESA_CONFIRMATION_RECEIVER_INVENTORY_RESULT.md) · [Timing check](external-imu-data/ESA_CONFIRMATION_TIMING_RESULT.md)

Seven groups can reveal whether a frozen method carries over to other flights. Even if all seven pass, they are too few to establish 95% prediction coverage with 95% confidence by counting alone. [What the flight count can establish](PREDICTION_GROUP_COUNT.md)

## Questions that guide the work

| Question | Current evidence | Remaining check |
| --- | --- | --- |
| Which part of the shape comparison comes from the gyroscope? | In the available acceleration-only checks, uncertainties in motion and orientation leave the shape unresolved. Full-IMU comparisons show a larger separation. | Quantify the gyro contribution with matched fields and independently supported measurement-error limits. [Measurement contribution](ilvis0-measurement-contribution/README.md) |
| Can the models predict positions left out of fitting? | NASA retrospective forecasts and one ESA development flight show a globe advantage in several matched comparisons. Some fits or accuracy checks remain unresolved. | Test a fixed error model and accuracy rule on separate flights. [Prediction evidence](PAPER_DATASET.md#prediction-evidence-kept-separately) |
| How certain is a result across flights? | The software checks the order of decisions and counts related recordings as groups. Generated-data validation passed under its stated conditions. | Calibrate the whole decision rule for aircraft, including shared errors and failed fits. [Decision method](PREDICTION_GROUP_DECISION.md) |
| What angular field do the recordings imply? | The NASA comparisons favor a specified field over zero once globe is preferred. | Estimate the field’s magnitude and direction freely. Solar versus sidereal rate is a later precision question. [Rotation field](ROTATION_FIELD.md) |

[Technical milestones](ANALYSIS_ROADMAP.md#current-milestones-and-finish-line) · [Study index](STUDIES.md) · [Earlier development checks](DEVELOPMENT_STUDY_HISTORY.md)
