# Check ground gyro variation against force direction

Use both previously selected low-speed stops in opened ESA recording 187.
They show substantial gyro variation while reported ground speed is low.
Test whether the logged gyro changes predict changes in the direction of the
recorded accelerometer vector. At low linear acceleration this direction gives
an approximate tilt reference. It is insensitive to rotation around that axis,
and acceleration or errors shared by both sensors can also change the result.

- Verify the original file hash and both sealed raw time ranges. Decode the
  exact recorded intervals between the first and last timestamps without
  filling gaps. Time-average the original three-axis acceleration over all
  complete one-second bins starting at the first timestamp. Assign each mean
  to the bin center and normalize it to a unit direction.
- Integrate the uncorrected, left-held gyro rates with their original sample
  durations between adjacent centers. Predict each later direction by applying
  the inverse body rotation to the earlier one. Compare one-second pairs and
  nonoverlapping ten-second pairs starting at the first center. Compose the
  same one-second rotations for the ten-second check.
- Score each pair against a no-change prediction. Report the actual direction
  change, gyro-predicted change, angular error and mean force magnitude at the
  centers. Compare centered changes in three components and report their
  similarity and the error reduction relative to no change. Centering is
  descriptive and removes constant changes from both series. Preserve the
  uncentered errors and every complete comparison.

This is a same-instrument motion check, with no fitted bias, frame alignment,
Earth rate, selection by gyro size or calibrated error limit. Agreement can
support an airframe-tilt contribution to the logged variation. Disagreement
leaves acceleration, yaw and instrument effects unresolved.

Freeze one task with one worker and one numerical thread. Permit one hash pass
over 1,100,258,400 bytes and exactly two declared input slices comprising
1,365,152 intervals. Charge one pass for decoding, one for reducing force
samples and one for integrating and comparing the gyro changes. Use a
120-second limit. No network operations, reserved-group reads or global model
fits are part of the task.
