# Boundary-aware nonlinear controls

This completed software matrix uses ten known-answer controls, four fixed starts
and three numerical strategies. It reads no NASA recordings and changes no archival results.

| Strategy | Fresh stopping checks | Known-answer qualification | Actual evaluations |
|---|---:|---:|---:|
| rectangular | 35/40 | 35/40 | 332 |
| snapped_rectangular | 38/40 | 38/40 | 346 |
| boundary_bvls | 40/40 | 40/40 | 218 |

Qualification checks both the existing fresh stopping tests and recovery of the
known objective and predicted observations. Unique well-conditioned cases also
check the parameters. A solver stopping successfully is insufficient by itself.

| Control | Original | Snapped start | Bounded linear steps |
|---|---:|---:|---:|
| interior | 4/4 | 4/4 | 4/4 |
| boundary | 3/4 | 4/4 | 4/4 |
| redundant | 3/4 | 4/4 | 4/4 |
| scaled | 4/4 | 4/4 | 4/4 |
| nonlinear | 4/4 | 4/4 | 4/4 |
| gain_offset | 4/4 | 4/4 | 4/4 |
| curved_boundary | 3/4 | 4/4 | 4/4 |
| exponential | 4/4 | 4/4 | 4/4 |
| curved_redundant | 3/4 | 4/4 | 4/4 |
| nonlinear27 | 3/4 | 2/4 | 4/4 |

The matrix used 896 actual evaluations, within its 24,000-call ceiling.
Every run retained its own 200-call limit, including fresh final checks.
No failure or poor start was retried.

The new candidate passes this software matrix.
Its bounded linear steps are checked against the actual nonlinear cost; rejected
steps are shortened. Only boundary slack of at most one trillionth in normalized
coordinates is snapped. Physical parameter limits and stopping thresholds are unchanged.

These are controls with exact derivatives and known answers, not qualification
on the much larger archival observation model. They establish neither statistical
significance nor recovery of any of the 41 unresolved stretches. A separate finite
observed trial would be needed before rollout.

The saved [results](controls.json), [per-run table](controls.csv) and
[receipt](receipt.json) preserve parameters, costs, stationarity, fresh checks,
evaluation counts, source hashes and the numerical environment.
The [fixed plan](PLAN.md) defines the comparison. Default report regeneration reads
the saved results only; it performs no optimization.
