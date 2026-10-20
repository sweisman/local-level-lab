# Streaming source-reference qualification

6/6 generated sources pass every midpoint/end reference check.

| Candidate / removal | Passed | Maximum value difference (m/s²) | Maximum coefficient difference | State bytes |
|---|---|---:|---:|---:|
| Globe with specified field / zero | Yes | 2.831734e-14 | 4.534846e-15 | 10768 |
| Globe with specified field / profiled | Yes | 2.831734e-14 | 4.534846e-15 | 10768 |
| Globe with zero field / zero | Yes | 2.831734e-14 | 4.534846e-15 | 10768 |
| Globe with zero field / profiled | Yes | 2.831734e-14 | 4.534846e-15 | 10768 |
| Flat disc / zero | Yes | 2.831734e-14 | 4.534846e-15 | 10768 |
| Flat disc / profiled | Yes | 2.831734e-14 | 4.534846e-15 | 10768 |

Checked 9,600/9,600 compiled source steps, 9,600/9,600 independent steps, and 3,225,600/3,225,600 scalar comparisons. Elapsed 18.82 seconds.

The compiled calculation uses unchanged native tangent primitives. The independent calculation uses quaternion rotations and analytic Jacobians; local controls also use complex-step matrix exponentials. Both phases of every packet retain all 27 physical columns and the native clock branch. The fixed-size derivative state avoids a recording-size output tensor.

Array-stream hashes and selected prefixes are preserved. This qualifies source reference rows only. The tighter norm-constrained body interval has not yet been connected to full dynamic propagation. No full native trajectory, aircraft observation, protected ESA data or optimizer was used. Whole-program floating-point enclosure and observational coverage remain unqualified.

[Frozen scope](PLAN.md) · [Source reference](../ilvis0-source-reference/README.md) · [Next task](NEXT_PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
