# Second low-speed iMAR baseline

The [receiver-only selection](SECOND_GROUND_INTERVAL_RESULT.md) found a second
ground interval in the opened ESA recording. This audit then read the matching
raw iMAR samples with the same parser and summary calculation used for the
[first ground interval](GROUND_IMU_RATE_RESULT.md). It verified the original
file hash and kept every sample in the preselected time range. The complete
[result](second-ground-imu-result.json) includes minute means, source hashes
and exact time bounds.

| Receiver-selected interval | First stop | Second stop |
|---|---:|---:|
| Location | 64.191° N, 51.676° W | 64.132° N, 21.946° W |
| Overlapping raw IMU time | 45.1 min | 30.7 min |
| Raw IMU samples | 811,809 | 553,345 |
| Mean instrument-axis rate X, Y, Z | −6.82, +2.24, −14.72 °/h | +1.50, −5.66, −11.91 °/h |
| Magnitude of mean rate vector | 16.37 °/h | 13.27 °/h |

The second magnitude is 3.10°/h smaller. The difference between the two
instrument-axis mean vectors is 11.82°/h. The second stop's two half means
differ by 3.74°/h. Its last 44.5-second minute bin has a Z-axis mean of
+55.79°/h even while receiver ground speed is low. That visible motion is
retained, not trimmed after inspecting the gyro. The median across its 30
complete minute means is approximately (+1.09, −5.87, −13.47)°/h.

These are recorded sensor-axis rates, including platform motion, instrument
offsets and any upstream processing. Aircraft heading and mounting alignment
at the two stops are not established. Low receiver speed does not rule out
aircraft yaw. The near-equal latitude therefore does not make the two vectors
direct measurements of one geographic field. No background rate, sensor bias
or Earth model was fitted, and no reserved ESA flight group was opened.

The changed vector and substantial within-stop variation make a simple
ground-average subtraction unsuitable for a solar-versus-sidereal rate test.
The next useful constraint is independent orientation and motion information
for these stops, or a designed reversal control. The aircraft prediction
error law remains unqualified.
