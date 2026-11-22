# Raw gyro variation over 1, 10 and 60 seconds

The [fixed plan](GROUND_RATE_SCALE_PLAN.md) reapplied the strict raw iMAR
parser to the opened ESA development recording. Both low-speed intervals had
been selected from receiver data before their gyro values were inspected.
The audit verified the original file hash, retained every selected sample,
and reproduced the earlier 60-second bin means. Its complete
[numerical result](ground-rate-scale-result.json) records every bin mean and
the source and method hashes. Five focused software checks passed.

The table gives **adjacent-bin Allan variation** of the unadjusted gyro
rate on each instrument axis, in degrees per hour. It describes how much
successive averages change; it is not a claim about instrument accuracy.

| Ground stop | Average length | Complete bins | X | Y | Z |
|---|---:|---:|---:|---:|---:|
| First | 1 s | 2,706 | 838.25 | 78.20 | 137.76 |
| First | 10 s | 270 | 93.56 | 15.59 | 18.83 |
| First | 60 s | 45 | 15.92 | 3.52 | 2.45 |
| Second | 1 s | 1,844 | 161.33 | 37.25 | 40.04 |
| Second | 10 s | 184 | 19.11 | 7.98 | 5.64 |
| Second | 60 s | 30 | 3.66 | 2.96 | 0.73 |

The strong changes with averaging time and differences between stops do not
support assigning one simple white-noise number to this logged stream.
The largest one-second mean in the first stop reaches +4,180°/h on X;
it remains in the result. Individual short-time rates can reflect airframe
vibration or turns despite low GPS ground speed. Sensor behavior, mounting
motion and onboard processing have not been separated from platform motion.

This is a source-specific **observed variation** diagnostic, useful when
designing later stress tests. It does not supply a sensor-only error law,
an independent Earth-rate estimate, a flight prediction interval or a
solar-versus-sidereal measurement. No model fit or reserved ESA group was used.
