# Check predicted force directions with the separate RF04 attitude record

Reuse the saved IMU21 force samples and two GPS trajectory reconstructions
from the [recorded motion-rate check](RECORDED_MOTION_RATE_RESULT.md). Keep
the earlier and later windows, both packet clocks, and all four matched
shape and background-field settings. Retain a force sample only when its
recorded packet midpoint is within 5 ms of a whole-second RF04 report.
Use the reported attitude at that second without interpolation and keep
the same matched samples for all models within each clock.

For each model, rotate the required local north/east/down force into the
aircraft frame using the RF04 roll, pitch and true heading. Fit one constant
proper rotation between that prediction and the measured accelerometer
directions on the earlier samples only. Use it without adjustment on the
later samples. Report earlier and later direction errors, the rotation
identifiability check and the later differences between model predictions.
Report separations both before and after the earlier mounting alignment.

This check uses the second inertial reference and its navigation conventions.
The errors cover the combined effects of receiver differentiation, attitude,
timing and accelerometer measurements. The 5 ms near-match, per-sample
force model and earlier mounting adjustment are diagnostic assumptions.
The experiment does not infer attitude from acceleration alone, provide an
absolute error bound or decide shape. It adds no observations to the original
gyro-free score.

Use one task and one numerical thread, with 41 charged operations, at most
15,856 replayed force evaluations and at most 443 rows per comparison.
Use a 90-second cooperative cap and bind the original force replay, the
completed RF04 intake and matching receipt, and qualified task recovery.
Zero original IMU decodes, Earth-model fits and reserved ESA reads.
[RF04 matched motion](RF04_MOTION_MATCH_RESULT.md)
