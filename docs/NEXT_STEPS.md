# What comes next

The main airborne comparison is complete: all **53 preselected stretches favor
the globe** under both tested processing assumptions. The next work asks what
creates that separation, whether the fitted models predict unused observations,
and how much confidence the measurements support.

An **IMU (inertial measurement unit)** records turning and acceleration. The
gyroscope is the central turning observation; accelerometers and receiver
positions help reconstruct and constrain the aircraft's motion.

[Verified findings](CURRENT_STATUS.md) · [Studies and what each added](STUDIES.md) ·
[All stretches](ilvis0-current-findings-20261015/STRETCHES.md) ·
[Comprehensive CSV](ilvis0-current-findings-20261015/stretch-analytics.csv).

## Numerical recovery is complete

The original run completed twelve comparisons. All 41 formerly unfinished
stretches now have separately checked recoveries using the same selected
observations and physical assumptions. Earlier failures remain preserved.
These are stages of one analysis, not additional independent flights.

There is no remaining recovery population in the main 53-stretch comparison.
Numerical completion is separate from physical adequacy, prediction and
calibrated statistical significance.

## Then: strengthen the interpretation

The [measurement-contribution work](ilvis0-measurement-contribution/README.md)
has reached these milestones:

| Completed check | What it established or left open |
|---|---|
| Saved-position scoring on eighteen stretches | All 36 horizontal-only processing-case comparisons favor globe at the existing parameters. This did not refit any model. |
| First horizontal-only refits | The 9.75-minute IMU8 stretch passed all six repeats and favored globe. The 4.07-minute IMU21 stretch remained unresolved at repeat precision. |
| Matched timing search | Both controls and 37 of 38 fits passed individually, but only two of six selected repeat comparisons agreed. The IMU21 sensitivity result remains unresolved. |
| Channel-removal software controls | All 25 checks pass. They define the ambiguity left without gyroscopes and an acceleration-magnitude diagnostic that does not use fused attitude. |

Removing height from the score also permits implausible vertical paths. Even
repeatable horizontal fits can reconstruct the wrong altitude by hundreds of
metres or more. Those are errors in the reconstructed path, not measured
aircraft altitude changes. This limits what the sensitivity check establishes;
it does not reopen the original full-position comparisons.

The next sequence is:

1. **Qualify the channel comparison.** Check the acceleration-only diagnostic on
   independently generated trajectories. Specify receiver-trajectory
   differentiation, its uncertainty and calibration assumptions before applying
   it to recordings. An omitted gyro stream cannot be replaced with fused attitude.
2. **Run a finite matched recorded-data check after qualification.** Reuse
   preselected intervals, preserve failures, and compare all candidates under
   the same declared assumptions. A wider timing search is deferred.
3. **Test prediction and uncertainty.** Estimate nuisance parameters using only
   training observations, predict separate time blocks or supported independent
   flights, and model residual correlation. Earlier split-recording trials provide
   development evidence but do not complete this validation.
4. **Account for shared observations.** Group simultaneous recorders, repeated
   stretches, flights and supported instrument installations before claiming
   independent replication.

The [channel-control plan](ilvis0-measurement-contribution/CHANNEL_CONTROLS.md)
and [technical roadmap](ANALYSIS_ROADMAP.md) give the implementation requirements.
Exact instrument documentation is supporting work, not a reason to suspend
analysis with clearly stated assumptions.

## Measure the rotation field freely

All 53 main comparisons also prefer the specified background field over zero.
That does not freely measure its rate or identify its cause.

The [rotation-field follow-up](ROTATION_FIELD.md) will estimate the retained
field's size, direction and geographic pattern, fitting aircraft motion,
transport, timing and calibration jointly. The available latitude, heading and
instrument coverage must first show which quantities can be separated. An
unknown field removed onboard cannot be estimated independently of the original
field without additional constraints.

### Solar versus sidereal rate

The targets are **15.0000 degrees/hour** for a mean solar day and about
**15.0411 degrees/hour** for a sidereal day: only 0.27% apart. The current
comparison fixes its background rate and has not measured that difference.

A dedicated precision study needs longer supported records, a freely estimated
rate, and uncertainty that accounts for gain, clock, instrument offsets and shared
processing. If precision is insufficient, the result will report that limit.

## Longer records and the ground experiment

The [additional-source inventory](external-imu-data/README.md) includes one
inspected 8.49-hour ESA survey recording with matching GNSS positions and a
19.28-minute Wuhan airborne sample. Neither has been added to the model comparison.
Each needs its own eligibility and observation-model qualification; the original
700 km/h rule is not automatically transferred to slower surveys.

The [stationary experiment](STATIONARY.md) remains secondary and under development.
It uses consumer IMUs on solid supports with repeated 180° reversals. Sensitivity,
alignment and uncertainty need physical validation before geographic pooling or
detection claims. The current stationary analyzer always abstains from a scientific
decision.

[Method](METHODOLOGY.md) · [Study index](STUDIES.md) · [Detailed roadmap](ANALYSIS_ROADMAP.md).
