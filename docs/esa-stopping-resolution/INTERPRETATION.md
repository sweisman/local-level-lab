# What the stopping diagnostic established

All 24 saved calibrations were checked without fitting them again. Each received
two identical calculations, the original bounded stopping correction, and seven
smaller or reversed corrections. The run used 240 calculations in 21.90 minutes.
Only the earlier training measurements were used.

Every saved cost was reproduced exactly. Repeated residuals and derivatives
were identical. The original outcomes also repeated: eight numerical passes,
seven cost-stability failures and nine position-stability failures.

The seven cost failures all concern the globe model with the specified background
field. Across all eight saved fits of that model, even the largest local position
change is below 4 micrometres. The cost changes can nevertheless exceed the
unchanged stopping tolerance. Smaller corrections do not consistently produce
smaller changes, and the local derivative predicts much smaller cost changes.

This points to a numerical-resolution question. Exact repeats rule out random
run-to-run differences; they do not prove that roundoff is the cause. Finite
precision, nonlinear behavior and branches in the calculation still need to be
distinguished. The next test checks precision on independent known-answer
examples before comparing calculations at these same saved points.

No failed fit becomes accepted. The one complete, adequate three-model setting
from the [height-gravity pilot](../esa-observed-height-pilot/README.md) remains
the available ESA development comparison. Seven separate confirmation groups
remain protected. This diagnostic adds no confidence estimate or independent
flight replication.

[Verified report](README.md) · [Every saved point](fixed-points.csv) ·
[Stopping checks explained](../NUMERICAL_STOPPING.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
