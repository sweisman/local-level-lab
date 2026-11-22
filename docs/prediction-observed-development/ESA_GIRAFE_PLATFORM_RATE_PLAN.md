# Check the GIRAFE platform rate columns on their own clock

The campaign lists time-tagged acceleration and angular rates for the
stabilized platform. The saved excerpts have time followed by six unlabeled
numeric columns. Check whether the last three can predict changes in direction
of the first three using the platform's verified relative clock.
[Campaign data table](https://essd.copernicus.org/articles/17/1667/2025/#section3)

Use the three [saved raw excerpts](ESA_GIRAFE_PLATFORM_VERTICAL_HOLDOUT_RESULT.md)
after their existing overlap and guard. Use complete tenth-second, time-weighted
force averages. Integrate each candidate's left-held rates between adjacent
centers and predict the direction at the later center. Compare adjacent
directions and also centers one second apart, using the unchanged ground-tilt
comparison with the appropriate time scale.

On the first excerpt in byte order, test degrees per second and radians per
second, each in all 48 signed axis permutations. Use the smallest angular RMS
prediction error at tenth-second separation to choose the convention. Order
ties by the fixed loop order. Report all scores, including no-change errors
and a comparison at one second. Apply only the chosen convention to the two
remaining excerpts and report both results. An improvement at every excerpt
would support this convention as a same-instrument check. Linear acceleration,
platform control motion and weak sensitivity about the force axis can still
make a mapping ambiguous. This is a screen with no claim of verified gyro
calibration, absolute-time agreement or airframe attitude.

Freeze one local task with one worker and one thread, at most three 1 MiB
reads, at most 14,000 rows per read and 98 declared rate comparisons. Use a
120-second limit. No network access, iMAR reads, new model fits or reserved
flights enter this check. The original iMAR clock gate remains failed.
