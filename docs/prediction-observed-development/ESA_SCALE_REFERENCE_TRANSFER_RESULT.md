# Scales chosen for the ESA error reference transfer poorly

The continuous search put **all six donor windows** inside the error reference
in every fold. Only **three of eight omitted windows** met it under either
inertial measurement error law. The total held-out log score also worsened
compared with the earlier separate-quiet-scale rule. The method missed the
development gate.

| Scale selection rule | Donor result | Omitted windows inside the reference | Total omitted negative log score |
|---|---|---:|---:|
| Earlier separate quiet scales, shared motion scale | Minimize donor log score | 2/8 | −10,725 |
| Continuous quiet and motion scales by slot | All six donor windows inside the reference in each fold | 3/8 | −9,366 |

Lower log scores are better. The worst omitted score under the new rule was
976.08. The working reference runs from 290.94 to 437.69. Even with every
donor window inside that interval, the same scales can give more than twice
the upper reference for an omitted window. The two error descriptions agree
to the displayed precision. The forecast positions were unchanged.

## Searching all eight windows together

The best setting found with all eight windows available came within **0.74
score units** of the reference edges, with its quiet and motion height scales
at the allowed upper limit. Three scores fell just below the lower endpoint
and two just above the upper endpoint. An independent calculation reproduced
the same interval misses. This is a near miss within a finite search. The
[previous interval cover](ESA_AXIS_SCALE_COMPATIBILITY_RESULT.md) remains
unresolved and a globally compatible setting is still possible.

All ten tasks completed in 13 seconds. They verified the reference calculation
and its work allowance. No trajectory was refitted and no reserved flight was
opened. The eight windows still supply evidence from one development flight.

[Frozen method](ESA_SCALE_REFERENCE_TRANSFER_PLAN.md) ·
[All settings and scores](esa-scale-reference-transfer-result.json) ·
[Verified run evidence](esa-scale-reference-transfer-evidence/README.md)
