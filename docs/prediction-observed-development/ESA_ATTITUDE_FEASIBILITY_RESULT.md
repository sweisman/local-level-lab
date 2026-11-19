# Earlier GPS excludes 17 of the 26 high-bound ESA calibration ranges

The [feasibility check](ESA_ATTITUDE_FEASIBILITY_PLAN.md) proved that
17 ranges cannot meet the earlier GPS loss allowance together with
their saved calibration constraints. All eight ranges that kept
their parent bound in the previous refinement were among them.

| Candidate | High-bound ranges checked | Excluded | Cover upper bound before | Cover upper bound after |
| --- | ---: | ---: | ---: | ---: |
| Zero-field globe | 12 | 8 | 26.734 | 20.850 |
| Zero-field disc | 14 | 9 | 34.241 | 33.164 |

The combined upper bound fell from **60.97 to 54.01 standardized
units**. The forecast difference is **25.41 units**. All exclusions
use the earlier loss certificate. The static constraints alone
provided no exclusions. Every range with a verified feasible point
remains in the cover.

Nine high-bound ranges remain. Two contain an archived feasible point.
The other seven lack an exclusion proof and keep their previous bounds.
Start with those nine ranges for the next score calculation. Use
the earlier-loss minimum as a starting point and scale the linear
constraints in the score proposal to match the feasibility check.
The physical-map allowance and full-flight prediction error remain
open. [Frozen plan](ESA_ATTITUDE_FEASIBILITY_PLAN.md)

[Sealed inputs, constraints and results](esa-attitude-feasibility-evidence/README.md).
Replay the exclusion proofs with the `verify` command in place of
`report`, under the one-thread numerical launcher. That replay uses
the saved weights and no optimization.
