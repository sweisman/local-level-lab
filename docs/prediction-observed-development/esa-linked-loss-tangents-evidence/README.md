# Loss-ball tangents leave the calibration bounds unchanged

The linear-programming method produced a score proposal for all eleven
surviving calibration ranges. The exact checks tightened none of their
existing bounds. The combined upper bound stayed at **53.20 units**
against the **25.41-unit** forecast gap.

| Zero-field candidate | Ranges checked | Bounds tightened | Combined-cover upper bound |
| --- | ---: | ---: | ---: |
| Globe | 5 | 0 | 20.649 |
| Disc | 6 | 0 | 32.546 |

All searches reached the 16-iteration cap. The linked certificates were
checked in the original physical coordinates against the saved feasible
points. The retained bounds and earlier exclusions stayed in force. A
generated case verified that the normalized proposal yields the known
support bound when checked in the original coordinates.

The run completed all 22 charged calculations without new trajectory
fits or reserved-flight reads. This leaves the static calibration bound
open. It also leaves the full integration remainder and aircraft error
coverage open.

[Frozen plan](ESA_LINKED_LOSS_TANGENTS_PLAN.md) ·
[Each proposal and retained bound](esa-linked-loss-tangents.json) ·
[Verified evidence bundle](esa-linked-loss-tangents-evidence/replay.zip)
