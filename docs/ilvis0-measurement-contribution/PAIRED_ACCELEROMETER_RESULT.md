# How closely do two accelerometers on the same aircraft agree?

The two IMU21 recordings agreed much more closely than the IMU8 and IMU21
recordings on the other flight. At one second, their later differences were
0.0018 and 0.0243 m/s² RMS respectively, after removing the mean difference
measured earlier on each leg. Both clocks gave nearly the same result.

| Time averaged | IMU8 and IMU21 difference (m/s² RMS) | Two IMU21 recordings difference (m/s² RMS) |
|---:|---:|---:|
| 0.05 s | 0.13488 | 0.02618 |
| 0.25 s | 0.04920 | 0.00612 |
| 1 s | 0.02430 | 0.00184 |
| 10 s | 0.00722 | 0.00017 |
| 30 s | 0.00390 | 0.00011 |

The table uses packet-header elapsed time. The common legs lasted 552 and 506
seconds. The earlier mean differences were about −0.106 and +0.0006 m/s². The
one-second values use 275 and 252 later windows. The 30-second values use eight
and seven. Both comparisons used the original signed accelerometer counts and
excluded gyroscope measurements from the calculation. Two of two tasks passed
with zero errors and zero Earth-model fits.

The measurements show how quickly between-recorder differences shrink when the
data are averaged. This can help test a proposed error model. The two recorders
can share errors from aircraft motion or processing. They can also differ due to
calibration, timing or where they were mounted. The study leaves absolute sensor
error and motion within a packet unresolved. It leaves the shape decision open.

## Implications for an error model

If the recorder difference behaved as independent noise with constant variance,
its RMS would scale approximately as the inverse square root of averaging time.
Using the measured one-second RMS to set that scale, the mixed pair's 10-second
RMS is 0.94 times the formula's value. For the two IMU21 streams it is 0.29 times
that value. Their 50 ms RMS values are 1.24 and 3.18 times the formula's values,
respectively. The results are similar under either clock. This is a descriptive
check of the paired difference, using the later one-second result as the
reference. It provides no calibrated probability and cannot separate correlated
sensor errors from differences in timing or motion at the two mounts.

If both adjusted recordings are required to track the same one-second reference,
at least one must differ from it by half their pairwise RMS or more. Those
conditional minimum disagreements are 0.0122 and 0.00092 m/s². The comparison
does not bound errors the two recorders share.

[Frozen method](PAIRED_ACCELEROMETER_PLAN.md) ·
[All timings and differences](paired-accelerometers-result.json) ·
[Verified run evidence](paired-accelerometers-evidence/README.md)
