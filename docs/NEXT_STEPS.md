# What comes next

The fitted comparison is complete for the 53 selected NASA stretches. The globe with the specified background field had the lowest fitted cost in every stretch under both processing assumptions. Later GPS positions have also been predicted successfully on several development flights. The next milestone is a test on independent flights with a justified error model. [Verified findings](CURRENT_STATUS.md)

An [adversarial review](red-team-20261125/README.md) of the saved fits found no error in the equations or the file decoding. It identified three weaknesses that the existing archive can address, listed below.

## Checks that can run on the existing archive

None needs data from another group. Check 1 is complete. Checks 2 and 3 are running. Check 4 is proposed.

1. **Repeat the selection without the navigation-status flag. Done.** Every stretch in the 53 comes from a file where the instrument's own navigation computer, which uses globe equations, reported full alignment throughout. Repeating the published rule on all 232 files without that requirement reproduced all 53 stretches and found 16 more intervals. All 16 come from a second recorder on the 2011 and 2015 flights. Fourteen overlap a published stretch on the same flight, and two add 14.2 minutes of flight time. Seen through GPS alone, 14 of the 16 were flown as steadily as the published stretches and two are just outside on one measure. None is fitted yet. Each first needs a check of the information it carries about the fitted parameters. [Result](ilvis0-highspeed-alignment-ablation/RESULT.md) · [GPS-only motion](ilvis0-highspeed-alignment-ablation/RECEIVER_MOTION_RESULT.md)
2. **Allow larger gyro offsets. Running.** Every fit of the 53 stretches let each gyro be off by up to 1°/hour. On one straight leg, a disc with a pitch-gyro offset near 7.5°/hour would be hard to tell from a globe. The saved globe fits needed offsets of about 0.1°/hour that did not change with speed, which argues against that explanation. Refitting the longest stretch on each of the 27 flight dates with allowances of 3, 10 and 30°/hour shows it directly. [Fixed plan](ilvis0-stretch-checks/GYRO_ALLOWANCE_PLAN.md)
3. **Give the disc the background field on all 53 stretches. Running.** The globe was fitted with and without the field. The disc was fitted with it on 4 of 27 recording groups. Completing the set shows whether the disc loses on shape or on the missing field. [Fixed plan](ilvis0-stretch-checks/DISC_FIELD_PLAN.md)
4. **Measure the radius and the rotation rate.** Fit the curvature and the background rotation freely and report both with their spread across flight dates. [Rotation field](ROTATION_FIELD.md)

A further check used data that is already published. The aircraft's own one-second flight record, used earlier for flight RF04, covers 32 of the 53 stretches. On all 32, its separate GPS track agrees with the instrument's to about a metre across the direction of flight. The two systems label time about 0.4 s apart. Once that is allowed for, their one-second turning agrees to a median of 0.014°. The remaining 21 stretches have no such record. [Aircraft-record comparison](ncar-aircraft-records/MOTION_MATCH_RESULT.md) · [Turning at the time difference](ncar-aircraft-records/MOTION_LAG_RESULT.md)

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
