# Complete-prefix physical source-value checks

**6/6 generated sources passed.**

| Candidate / removal | Result | Completed source steps | Scalar checks | Norm closures |
|---|---|---:|---:|---:|
| Globe with specified field / zero | Passed | 1600 | 19200 | 3200 |
| Globe with specified field / profiled | Passed | 1600 | 19200 | 3200 |
| Globe with zero field / zero | Passed | 1600 | 19200 | 3200 |
| Globe with zero field / profiled | Passed | 1600 | 19200 | 3200 |
| Flat disc / zero | Passed | 1600 | 19200 | 3200 |
| Flat disc / profiled | Passed | 1600 | 19200 | 3200 |

Charged 6/6 complete bounds and 19200/19,200 bound steps. Reserved 9,600/9,600 source-reference steps, 115,200/115,200 comparisons and 19,200/19,200 closures. Elapsed 45.79 seconds.

The reported arithmetic allowances include calibration, rotation-reference and matrix operations. Each completed comparison uses those allowances directly, without an added numerical margin. Hashes and selected prefixes preserve both streams. Failed attempts and reservations remain recorded.

This qualifies physical source values only. Training-derived acceleration constraints, explicit affine-reference rows and integration into complete position bounds remain separate gates. The existing trained-adapter point failures are unchanged. No full native trajectory, aircraft fit, protected ESA data or optimizer entered this study. Whole-program floating-point enclosure and observational coverage remain unqualified.

[Frozen scope](PLAN.md) · [Source rounding work](../ilvis0-body-interval/ROUNDING_PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
