# Does five-epoch training constrain the linear prediction?

This saved-data diagnostic isolates training leverage from the large nonlinear approximation bounds. It uses all 27 physical derivative columns at the original expansion, with ±1 m training changes at five epochs. It omits shared and nonlinear errors. It is not a replacement prediction interval or an aircraft result.

| Processing | Feasible north spread | East spread | Height spread |
|---|---:|---:|---:|
| Zero removal | 420.263 m | 747.100 m | 39.927 m |
| Profiled removal | 445.141 m | 1,068.424 m | 54.499 m |

The spreads come from two exactly verified feasible points per axis, not an assertion that the LP found an exact optimum. Each point stays inside the original physical box and the affine training-change limits. Nonlinear feasibility is not established; a large affine spread is a geometry warning, not proof that the full prediction target is impossible. A small spread would not bound the entire family.

No new integration, aircraft fitting or active-shard merge is performed. The running study, its targets and all earlier outcomes remain unchanged.

[Fixed diagnostic scope](PLAN.md) · [Long-record first pair](../ilvis0-long-staged-feasibility-v2/FIRST_PAIR.md).
