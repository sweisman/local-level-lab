# A shared GPS correction removes the recorded force-only gaps

One GPS position correction removed all **16** remaining IMU8 gaps in
the original force-only check. The largest change at any receiver epoch
was **0.272 m**. The calculation used the same correction across all four
physical models, both clocks and all 608 windows. It kept each model's
earlier-only accelerometer gain fixed. IMU21 cleared the original check
at every window with zero position correction.

| Recorder | Force inequalities | Original gaps | Gaps after the correction | Gaps against the lower force bound |
| --- | ---: | ---: | ---: | ---: |
| IMU8 | 4,864 | 16 | 0 | 5 |
| IMU21 | 3,064 | 0 | 0 | 4 |

The final check recalculated the original nonlinear force intervals. The
original comparison clears when the accelerometer lower bound is no
higher than the upper end of the predicted force interval. Comparing
against the lower end is more demanding and leaves the nine small gaps
shown in the last column. The IMU8 correction has a covariance norm of
0.225 under the stated error law. This is a constructed example, and its
size gives no estimate of the GPS error that actually occurred.

For comparison, the [saved IMU forecast test](MATCHED_FORECAST_RECEIVER_RESULT.md)
found that, on IMU8, the specified-field globe and disc forecasts would
need at least 12.06 m of additional horizontal receiver error per epoch
to tie over the first 30 seconds. That test held both forecasts fixed.
The force-only result uses one necessary condition and leaves orientation
and continuous aircraft motion unresolved. Together, the tests show that
the force-only and complete IMU comparisons respond differently to small
changes in GPS position. The gyroscope's separate contribution still
needs a matched comparison with independently supported motion limits.

[Applying this exact correction to the saved forecasts](SHARED_FORCE_FORECAST_RESULT.md)
left every paired ranking unchanged at all four horizons.

The first IMU8 task reached its time limit while computing gradients.
The separate IMU8 run computed only the 16 gradients needed to propose
the correction and rescored all 4,864 inequalities. It finished in 32.4
seconds. The original IMU21 result and the stopped task are preserved.
The checks use no gyroscope observations or new navigation fits.

[Original plan](SHARED_FORCE_WITNESS_PLAN.md) ·
[Faster IMU8 plan](SHARED_FORCE_WITNESS_V2_PLAN.md) ·
[Verified result summary](shared-force-witness.json) ·
[IMU21 and original timeout](shared-force-witness-v1-evidence/replay.zip) ·
[Completed IMU8 evidence](shared-force-witness-v2-evidence/replay.zip)
