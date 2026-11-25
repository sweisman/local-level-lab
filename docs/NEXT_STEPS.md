# What comes next

The fitted comparison is complete for the 53 selected NASA stretches. The globe with the specified background field had the lowest fitted cost in every stretch under both processing assumptions. Later GPS positions have also been predicted successfully on several development flights. The next milestone is a test on independent flights with a justified error model. [Verified findings](CURRENT_STATUS.md)

## What the next checks need

- **NASA RF04.** With RF04 attitude supplied, the force direction errors are about 0.17° for globe and 0.30° for disc. Plausible rounding and estimated antenna motion account for only part of the northward acceleration disagreement. The next check needs faster aircraft motion measurements or independently surveyed antenna locations. [Force predictions](ilvis0-measurement-contribution/RF04_FORCE_AVERAGE_RESULT.md) · [Antenna motion](ilvis0-measurement-contribution/RF04_ANTENNA_MOTION_RESULT.md)
- **ESA flight 187.** The platform’s time-stamped orientation could help check horizontal aircraft motion. The aircraft’s GPS receivers share one roof antenna, so we also need evidence that bounds their shared error. The two nearby ground stations covered the full two-minute comparison and differed by 6.54 mm RMS in matched satellite range changes. That comparison measures disagreement between ground stations. [Platform records](external-imu-data/ESA_GIRAFE_187.md#aircraft-motion-and-platform-state-in-the-two-minute-check) · [Ground comparison](prediction-observed-development/ESA_NUUK_CLOCK_AWARE_RESULT.md)

The NASA RF04 text file repeats the one-second attitude and GPS data already checked. A faster original motion record or verified antenna installation measurements remain the leads for that flight. All seven reserved ESA flight groups remain unscored. Their exact training and scoring times are ready to bind to a qualified plan. [RF04 file comparison](ilvis0-measurement-contribution/NCAR_RF04_INTAKE.md#what-the-nasa-text-file-adds) · [Confirmation preflight](external-imu-data/ESA_CONFIRMATION_PREFLIGHT.md)

Two alternate NASA flights supplied paired recorders for a separate
consistency check. A wider camera search found timed images for 17 of the 53
stretches. The reviewed previews did not show fixed features for an independent
motion measurement. [Paired recorders](ilvis0-measurement-contribution/MOTION_FALLBACK_RESULT.md) ·
[Camera search](ilvis0-measurement-contribution/CAMERA_CATALOG_SCREEN.md)

The [alternate archive screen](external-imu-data/ALTERNATE_ARCHIVE_SCREEN.md)
verified two raw gyroscope streams and a separate GPS solution in a public
Swiss drone sample. Its slow, short survey legs leave it as a software test
case. The Porto Galileo campaign has a stronger instrument setup, with raw
file access still open.

## Before confirmation

1. **Establish the error limits.** Use the independent checks to bound aircraft motion and GPS error. Check that those bounds apply under the conditions recorded on the reserved flights. [Evidence needed](ANALYSIS_ROADMAP.md#what-would-advance-the-next-test)
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
