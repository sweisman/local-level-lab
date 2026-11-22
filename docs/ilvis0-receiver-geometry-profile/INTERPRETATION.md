# What the longer tracks' geometry can and cannot separate

The fixed [29-track study](RESULT.md) compared predicted angular-rate patterns
for every model pair using the receiver paths. It did **not** score the
recorded gyroscope. All 29 source tasks passed; every pair/treatment result is
in the [table](geometry.csv).

The median fraction of predicted contrast left after nuisance projection was:

| Comparison | Constant bias | Bias and drift | Bias, drift, gain and mount tangents |
|---|---:|---:|---:|
| Specified-field globe vs flat | 0.000991 | 0.0000916 | 0.00000000143 |
| Specified-field globe vs zero-field globe | 0.0000454 | 0.00000320 | 0.00000000383 |
| Zero-field globe vs flat | 0.000569 | 0.000153 | 0.00000000126 |

The calculation takes the worst crab, roll, pitch and model anchor in its
declared envelope. With the widest **unbounded local** nuisance tangent,
nearly all rate contrast can be represented by calibration/mount changes on
these paths. The 12 tracks below both earlier motion reference values do not
improve that result: their median retained fractions under the widest tangent
are also below one part in a billion for all three pairs.

This is **not** a conclusion that the recorded fits are false or that no
airborne IMU can distinguish the models. The original complete fit uses
bounded calibration, acceleration and receiver-position constraints together.
This diagnostic uses angular-rate geometry alone, uniform weights and an
aircraft-motion term assumed independently removable. The data do not supply
that independent body rotation. A realistic, bounded, full-pipeline design
check is still required before any of these new candidates can be analyzed.
No candidate is promoted, no new Earth-model fit is run, and no statistical
power or significance follows from these fractions.
