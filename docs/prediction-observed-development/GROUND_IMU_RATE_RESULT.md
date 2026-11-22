# Raw gyro rates during the selected ground interval

The [fixed control](GROUND_IMU_RATE_PLAN.md) overlaps the receiver-selected
65-minute low-speed interval with the iMAR recording's published timestamps.
The IMU starts about 20 minutes after the receiver, leaving **811,809 raw
samples over 45.1 minutes** at effectively 300 Hz. The full original 1.02 GiB
IMU file passed its published SHA-256 check. No model was fitted and no
predicted rotation was subtracted.

| Raw instrument-axis statistic | X | Y | Z |
| --- | ---: | ---: | ---: |
| Mean rate over every selected sample | −6.82°/h | +2.24°/h | −14.72°/h |
| Median of 46 minute-bin means | −6.00°/h | +2.78°/h | −13.98°/h |
| First-half mean | −6.69°/h | +3.14°/h | −13.59°/h |
| Second-half mean | −6.95°/h | +1.34°/h | −15.84°/h |

The magnitude of the full mean vector is **16.37°/h**. It is on the scale of
a conventional approximately 15°/h background rate, but the vector alone
cannot identify its source or even isolate a background field. The instrument
axes have not been placed in a geographic frame, and sensor bias, upstream
processing, mounting and actual aircraft motion remain unresolved.
The two half-interval mean vectors differ by **2.90°/h** in magnitude. That
change mixes motion and instrument behavior; it is not a sensor-noise
specification. It is also far larger than the 0.041°/h solar-versus-sidereal
rate difference, so this single ground control cannot resolve that question.

Low GPS speed does not mean zero aircraft rotation. The X minute means vary
from positive to negative tens of degrees per hour. The final partial bin is
only about six seconds long and has a Z mean near −489°/h, consistent with a
brief substantial turn or handling event while the receiver speed remains
low. That bin and every original sample remain in the full mean; nothing was
trimmed after seeing the gyro. Acceleration magnitude averages 9.824 m/s²
and recorded temperature spans 35.70–35.87 °C, but neither proves the
mounting or yaw was static.

This control makes the logged angular-rate scale visible and shows why a
stationary-field analysis needs an independent attitude/motion control or a
carefully calibrated model of sensor-fixed bias. It cannot distinguish solar
from sidereal rates or decide between physical explanations of a rotation
field. The [saved report](ground-imu-rate-result.json) includes all 46 minute
means, timing, source/selection/parser hashes and the untrimmed mean. Fifteen
focused parser and aggregation tests passed.
