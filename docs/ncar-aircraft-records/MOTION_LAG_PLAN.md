# Plan: compare turning again at the time difference found in the GPS tracks

## Question

The [first comparison](MOTION_MATCH_RESULT.md) found the aircraft record
and the instrument a nearly constant fraction of a second apart along the
track: 0.39 s in 2011 and 0.44 s in 2015. It compared turning with the
gyro windows unshifted and 80 ms either way. Moving them later helped on
all 32 stretches. Does the turning match more closely when the gyro
windows are moved by the full time difference?

## What is compared

The same 32 stretches, aircraft records and recorded IMU data. An **IMU
(inertial measurement unit)** is the instrument whose gyroscopes and
accelerometers supply the measurements. The change in aircraft orientation
over 1, 5 and 10 seconds is compared with the rotation the gyros
accumulated, with the gyro windows moved later by three amounts fixed in
advance:

| Shift | Value | Why |
| --- | --- | --- |
| None | 0 s | Repeats the first comparison as a check. |
| GPS lag | Each stretch's own value from the first comparison, 0.39 to 0.45 s | Measured from the GPS tracks alone. It uses no rotation data. |
| One-second average | 0.49 s | Roll and pitch were sampled 50 times a second. An average over the labelled second has its middle 0.49 s after the label. |

No shift is tuned on the rotation data. Both packet clocks of the first
comparison are kept.

## How the result will be read

For every stretch the report gives the one-second, five-second and
ten-second RMS difference at each shift, and counts the stretches where a
shift lowers the difference. All three shifts are reported whichever is
smallest.

If the aircraft record is a one-second average, it also smooths the
motion, so some one-second difference will remain at any shift. A closer
match would support the reading that the two systems label time
differently. It would not show which label is right, and it sets no limit
on motion inside a second. No Earth model is evaluated and nothing enters
a fit.

## Limits and recovery

One worker with one numerical thread and a one-hour cooperative time
limit. Each stretch is one sealed task with a fixed number of charged
steps. Finished stretches are reused after a restart, and the shared
task-recovery procedure may rerun only unfinished stretches under its own
finite limits.
