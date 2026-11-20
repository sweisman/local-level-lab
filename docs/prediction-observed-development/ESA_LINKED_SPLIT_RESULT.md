# Splitting the calibration ranges leaves the overall bound unchanged

The subdivision ruled out three of 18 child ranges using the earlier
GPS fit. Each parent range still had at least one surviving child. The
combined bound stayed at **53.66 units**, above the **25.41-unit**
forecast difference. This check cannot establish that the difference
survives every allowed calibration.

| Zero-field candidate | Surviving parent ranges split | Child ranges excluded | Previous upper bound | Refined upper bound |
| --- | ---: | ---: | ---: | ---: |
| Globe | 4 | 2 | 20.65 | 20.65 |
| Disc | 5 | 1 | 33.01 | 33.01 |

Each range was split along the coordinate with the largest product of
its width and an upper bound on its score sensitivity. The two closed
children covered the full parent. The calculation applied the parent
range's saved score and fit-loss directions to each child. It kept all
previously feasible points and all stronger existing bounds.

All nine tasks completed, with 45 charged calculations and no new fits.
The study reused archived GPS fit constraints and read no later receiver
positions or reserved flights. It addresses the static calibration map.
The integration remainder and aircraft uncertainty remain open.

[Frozen plan](ESA_LINKED_SPLIT_PLAN.md) ·
[Bounds for all 18 children](esa-linked-split.json) ·
[Verified evidence bundle](esa-linked-split-evidence/replay.zip)
