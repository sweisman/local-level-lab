# Correct calculation, little improvement from the broad calibration boxes

All 48 sectors passed correctness and retained their declared generated truth.
The run reconciled 96 interval-map evaluations, 48 independent coupling audits,
288 LP proposals and 1,152 exact support checks. It took 141.4 seconds.

The complete calibration relationship improves widths by less than 0.12%.
Four of six groups meet the unchanged width target; both specified-field globe
groups still miss it. These are generated software cases: their range widths
describe the uncertainty calculation. The aircraft findings remain **53 globe
preferences, zero flat preferences**, with no new aircraft fit here.

The earlier extreme-point diagnostic established that the linear region admits
unrealizable error combinations. The complete-map constraints now preserve that
relationship, but their derivative bounds over broad calibration boxes remain
too loose to remove much of the unwanted freedom.

The [saved-only decomposition](DECOMPOSITION.md) finds the remaining affine
part is still important. In all 18 axes of the six known-feasible sectors, the
saved unshared/arithmetic allowance alone lies below the target. Those saved
allowances do not yet force a more expensive propagation-bound recalculation.

The next bounded test will divide the two mounting-angle coordinates not already
covered by the yaw sectors. Every smaller box must be retained or excluded by
the same checked constraints. No calibration point or future outcome may choose
the partition. This is a new freeze, not a retry or expansion of this completed run.

[Results](README.md) · [Range components](DECOMPOSITION.md) ·
[Next comparison](NEXT_PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
