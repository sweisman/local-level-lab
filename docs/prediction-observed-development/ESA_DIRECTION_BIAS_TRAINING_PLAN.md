# Estimate accelerometer X bias from earlier force directions

Reuse all 16 force supports, both averaging widths, three velocity sources
and three matched background settings from the completed direction transfer.
Freeze a grid from −0.10 to +0.10 m/s² in steps of 0.0005. Give each shape its
own bias and starting rotation. Use the first eight supports to choose both.
Minimize the root mean square chord distance between unit force vectors,
using one proper rotation per grid value and the earliest grid value on
an exact tie. Score the last eight supports once at the selected point.
Report angular differences in degrees for this retrospective forecast check.

To test whether the earlier directions disfavor the positive bias range
from +0.0225 to +0.10 m/s², bound the best training score between its grid
points. The minimized chord distance is Lipschitz in the normalized
measured vectors. Use the force-vector derivative bound and each cell's
half width. Report the gap from the grid winner and half that gap as the
largest bounded RMS chord perturbation that would keep the comparison in
the same direction. This describes a conditional margin under the stated
one-axis change and fixed predictions. If the margin vanishes, report that
the range remains unresolved. This test neither supplies a discrepancy
bound for real flights nor fixes the other calibration parameters.

Use the prior direction-transfer study's exact frozen inputs. Verify the
selection, predictions and frame calculations against the existing saved
references. Freeze 36 profiles with at most 401 training rotations and one
later score each, one thread and a 90-second ceiling. Read no reserved
flight groups or original forecast's later receiver positions. Do not make
a scientific decision from these one-flight scores.
