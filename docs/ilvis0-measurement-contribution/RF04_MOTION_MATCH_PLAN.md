# Compare RF04 and the recorded IMU21 motion on the same seconds

Use the original selected stretch on the Gulfstream V and the verified
RF04 excerpt for 12:05:40–12:13:02 UTC on 12 October 2011. First compare the
two independent receiver tracks at their unmodified common UTC times.
Report descriptive horizontal separation and change in receiver height
from the first common epoch. The receivers report different height datums,
so the latter is a comparison of changes only. Preserve unmatched seconds.

Compare attitude change from RF04 roll, pitch and true heading with the
ordered product of the original Group-4 rotation increments, in the
aircraft axes supplied by the recorded installation. Use consecutive,
disjoint windows of 1, 5 and 10 seconds starting at 12:05:40 UTC. Use
only complete IMU packets wholly inside each window, with at most 15 ms
uncovered at the edges. Report the omitted coverage and a three-axis
rotation-distance summary. Use both header-elapsed and nominal 200 Hz
packet clocks. The reported-time comparison is primary. Separately shift
the IMU windows by −80 and +80 ms to show sensitivity to the documented
lag magnitude. Report all cases without tuning alignment or rate offsets.

RF04 reports attitude in a navigation frame. Group 4 measures inertial
rotation under the tested decoder. Differences can include frame rotation,
instrument, timing and filtering effects. This is a motion cross-check
at the output cadence. It supplies no upper bound on subsecond aircraft
motion and adds no observations to the gyro-free model score.

One task, one numerical thread, 21 charged operations, at most 150,000
selected packets per pass, and a 90-second cooperative wall allowance.
Bind saved selection, original bytes, intake report, source, environment
and recovery qualification before launch. Zero Earth-model fits and zero
reserved ESA reads. [RF04 intake](NCAR_RF04_INTAKE.md)
