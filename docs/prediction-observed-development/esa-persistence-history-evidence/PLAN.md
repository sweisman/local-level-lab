# Carry recent motion across the forecast cut

The [forecast error audit](ESA_PERSISTENCE_WINDOW_DIAGNOSTIC_RESULT.md)
found excess error throughout one steady forecast. The sealed input
metadata record 49 intervals with above-threshold motion before that
forecast and zero for the other three steady cases. Check whether the
forecast started before the effect of that earlier motion had decayed.

Recover the original earlier inertial increments and query times for all
eight windows. Bind them to the archived training-prefix hashes and to the
400 earlier receiver times. Use the original angular exposure trigger and
15-second decay. Take the response at the final training report and carry
it forward from there. Compare against the original zero-state forecast.
Keep the six fitted error parameters from the completed donor fits, the
forecast mean and the extra covariance components fixed. This changes
only the initial motion weight for the native innovation law.

Replay both input conventions and all original scores. Require an absolute
replay tolerance of 0.000001. Report each training end weight, most recent
above-threshold interval, propagated weight and score change, including
any unchanged result. A score change tests this specific memory mechanism.
It does not reclassify the original outcomes or establish error coverage.

Freeze four tasks, one per pair, with two windows and both input
conventions. Use two one-thread workers, 40 charged calls and a 180-second
cooperative deadline. No parameters are fitted, and no reserved flights
are read. Check the state carried across the cut on generated controls.
