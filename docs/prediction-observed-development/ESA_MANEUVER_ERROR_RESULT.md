# A turn and a straight-flight control show different forecast errors

The additional 400-report ESA holdout on development recording 187
supplied a straight-flight control. The motion screen selected zero
repeat turns before reading the saved path. All 13 complete blocks
had ground-course spans below 1.0°. The longest held-out forecast
still missed height by **11.88 m RMS**, including **22.81 m RMS**
in the final complete 30-report block. Cross-track RMS grew from
0.013 m in the first block to 1.39 m in the final complete block.

The original 120-report windows also let us test a simple explanation
for the error that followed the [recorded turn](ESA_INNOVATION_TRANSFER_RESULT.md).
A constant heading step after report 60 was allowed to take its best
value under the original covariance. The same step time was used in
the earlier, quieter window.

| Window | Best heading step | Reduction in the full squared score |
|---|---:|---:|
| Earlier control | 0.000060° | 0.0046% |
| Later window with the turn | 0.00133° | 0.58% |

The two IMU error descriptions give the same figures to the displayed
precision. In the later window, the step raised physical east RMS
from 0.527 m to 0.544 m even as the weighted score fell slightly.
A persistent heading step explains little of the recorded increase
under these weights. The straight window also shows that substantial
forecast drift can develop during quiet flight. A prospective error
test should allow persistent drift in straight flight and separately
check a short-lived response to motion.

This is retrospective development evidence on one flight. The set
of saved paths did not contain a second qualifying turn and therefore
cannot establish that the turn-associated pattern repeats. Neither
analysis restarted a fit or opened a reserved flight group.

[Motion selection plan](ESA_MANEUVER_PAIRS_PLAN.md) ·
[All selected blocks](esa-maneuver-pairs-selection.json) ·
[Straight-flight errors](esa-maneuver-pairs-result.json) ·
[Heading-step plan](ESA_HEADING_STEP_PLAN.md) ·
[Heading-step scores](esa-heading-step-result.json)
