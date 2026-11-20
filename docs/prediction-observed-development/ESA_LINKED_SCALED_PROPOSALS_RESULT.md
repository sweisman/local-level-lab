# Rescaling helps two searches converge and leaves the overall bound unchanged

The normalized score search reported convergence on **2 of 11** surviving
calibration ranges. Exact certificate checks tightened three individual
bounds and excluded no additional ranges. The overall upper bound remains
**53.20 units** against the original **25.41-unit** forecast gap.

| Zero-field candidate | Children checked | Score searches converged | Individual bounds tightened | Overall upper bound |
| --- | ---: | ---: | ---: | ---: |
| Globe | 5 | 0 | 1 | 20.649 |
| Disc | 6 | 2 | 2 | 32.546 |

The earlier-loss search reached the iteration limit on every child. The
checks treated every approximate direction and multiplier as a proposal.
Only outward arithmetic in the original calibration coordinates could
tighten a bound. All saved feasible witnesses remained consistent with
the cover. A generated test checked that the rescaling preserves the
residual, score differences, local bounds and static inequalities.

All eleven tasks finished within the 44-calculation allowance. The
existing losses, score and static limits stayed fixed. The work used no
new fits, integration or reserved flights. The overall bound still
leaves separation under every allowed calibration unresolved.

[Frozen plan](ESA_LINKED_SCALED_PROPOSALS_PLAN.md) ·
[Per-child solver statuses and bounds](esa-linked-scaled-proposals.json) ·
[Verified evidence bundle](esa-linked-scaled-proposals-evidence/replay.zip)
