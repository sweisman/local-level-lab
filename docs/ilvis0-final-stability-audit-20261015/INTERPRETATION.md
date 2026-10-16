# What the saved evidence narrows down

The two affine solvers agree: both propose a decrease of about **0.00112024** in
the primary's local objective and **0.00088518** in the repeat's. Column scaling
changes those values by less than 0.000000000001. Neither local correction is
worse than the feasible zero step. A basic failed affine solve is therefore not
the explanation supported by this audit.

The preserved full-model histories show the opposite behavior for those complete
corrections:

| Endpoint | Current objective | Objective after the full correction | Accepted? |
|---|---:|---:|---|
| Primary | 1566.0795115433425 | 1566.082617773141 | No |
| Repeat | 1566.079511624779 | 1566.0822372136572 | No |

The largest normalized correction coordinate is **time offset**, accompanied by
initial horizontal position. The full corrections imply about +3.98 ms and −3.46 ms
of time-offset movement within the unchanged ±0.15-second allowance. The saved
endpoints themselves have almost identical fitted offsets: 0.1131511098 and
0.1131512051 seconds. Their close agreement is numerical repeatability, not a
measurement of timing accuracy.

This points toward examining the time-alignment direction and how its local
derivative behaves over a finite correction. Both saved endpoints record zero
receiver epochs exactly at packet boundaries; that does not establish smoothness
through a correction spanning several milliseconds. The audit does not establish
an interpolation defect, a processing correction or a cause in the physical data.

The next targeted check should compare the saved time-offset derivative with
bounded full-model perturbations at several small scales, and inspect the same
packet/time branches on both sides. That requires a new finite native-prediction
freeze, but no optimization. No further fit of this target is justified merely
by increasing the evaluation cap, and none is launched by this saved-only audit.
The unresolved label remains unchanged.

The [audit measurements](README.md), [original matched-trial results](../ilvis0-trust-trial-20261015/RESULTS.md)
and retained source artifacts provide the supporting record. The separate
[six-target assessment](../ilvis0-hybrid-remaining-20261015/README.md) can proceed
under the already qualified hybrid method without changing this target's checks.
