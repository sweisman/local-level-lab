# What comes next

The fitted comparison is complete for the 53 selected NASA stretches. The globe with the specified background field had the lowest fitted cost in every stretch under both processing assumptions. Later GPS positions have also been predicted successfully on several development flights. The next milestone is a test on independent flights with a justified error model. [Verified findings](CURRENT_STATUS.md)

An [adversarial review](red-team-20261125/README.md) of the saved fits found no error in the equations or the file decoding. It identified three weaknesses that the existing archive can address, listed below.

## Checks that can run on the existing archive

These are proposed. None has been approved or started, and none needs data from another group.

1. **Fit five unused NASA stretches.** An [earlier screen](ilvis0-alignment-ablation/RESULT.md) removed the requirement that the instrument's own navigation computer report full alignment and kept every other rule. It found five more stretches, 55 minutes in all, on four dates. They have never been fitted. Every stretch in the 53 comes from a file where that computer, which uses globe equations, reported full alignment throughout. Fitting the five with nothing else changed tests whether that requirement mattered, on recordings that played no part in development.
2. **Allow larger gyro offsets.** Every fit so far let each gyro be off by up to 1°/hour. On one straight leg, a disc with a pitch-gyro offset near 7.5°/hour would be hard to tell from a globe. The saved globe fits needed offsets of about 0.1°/hour that did not change with speed, which argues against that explanation. Refitting with allowances of 3, 10 and 30°/hour would show it directly.
3. **Give the disc the background field on all 53 stretches.** The globe was fitted with and without the field. The disc was fitted with it on 4 of 27 recording groups. Completing the set shows whether the disc loses on shape or on the missing field.
4. **Measure the radius and the rotation rate.** Fit the curvature and the background rotation freely and report both with their spread across flight dates. [Rotation field](ROTATION_FIELD.md)

A further check uses data that is already published. The separate one-second aircraft record used for flight RF04 exists for every flight of the 2011 and 2015 campaigns. It could extend the independent motion check from one stretch to as many as 41. [2011 aircraft records](https://doi.org/10.5065/D6R49P35) · [2015 aircraft records](https://doi.org/10.5065/D6H70D6N)

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

The error limits in step 1 come from a fine satellite-range score on one two-minute development comparison, where aircraft range error would need to stay near 2 mm. The position comparison between the three candidates is much coarser. In the two complete settings on the ESA development flight, the withheld horizontal errors were 5 m for the globe with the field, 2,590 m for the zero-field globe and 3,997 m for the disc. A confirmation rule built on position error could work with a coarse, stated GPS allowance, and would need a rule for disc fits that do not converge. Whether to use the reserved groups that way is an open decision. [ESA matched forecasts](prediction-observed-development/ESA_400_120_MODEL_MATRIX_INTERPRETATION.md)

Seven groups can reveal whether a frozen method carries over to other flights. Even if all seven pass, they are too few to establish 95% prediction coverage with 95% confidence by counting alone. [What the flight count can establish](PREDICTION_GROUP_COUNT.md)

## Questions that guide the work

| Question | Current evidence | Remaining check |
| --- | --- | --- |
| Which part of the shape comparison comes from the gyroscope? | In the available acceleration-only checks, uncertainties in motion and orientation leave the shape unresolved. Full-IMU comparisons show a larger separation. | Quantify the gyro contribution with matched fields and independently supported measurement-error limits. [Measurement contribution](ilvis0-measurement-contribution/README.md) |
| Can the models predict positions left out of fitting? | NASA retrospective forecasts and one ESA development flight show a globe advantage in several matched comparisons. Some fits or accuracy checks remain unresolved. | Test a fixed error model and accuracy rule on separate flights. [Prediction evidence](PAPER_DATASET.md#prediction-evidence-kept-separately) |
| How certain is a result across flights? | The software checks the order of decisions and counts related recordings as groups. Generated-data validation passed under its stated conditions. | Calibrate the whole decision rule for aircraft, including shared errors and failed fits. [Decision method](PREDICTION_GROUP_DECISION.md) |
| What angular field do the recordings imply? | The NASA comparisons favor a specified field over zero once globe is preferred. | Estimate the field’s magnitude and direction freely. Solar versus sidereal rate is a later precision question. [Rotation field](ROTATION_FIELD.md) |

[Technical milestones](ANALYSIS_ROADMAP.md#current-milestones-and-finish-line) · [Study index](STUDIES.md) · [Earlier development checks](DEVELOPMENT_STUDY_HISTORY.md)
