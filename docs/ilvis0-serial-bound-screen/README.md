# Serial execution of the unchanged calculation

6/6 cases passed; serial execution recipe qualified.

| Case | Bound seconds | Exact saved report |
|---|---:|---|
| serial-transform-full-0-0-0 | 38.123 | Yes |
| serial-transform-full-0-1-0 | 41.269 | Yes |
| serial-transform-full-1-0-0 | 40.294 | Yes |
| serial-transform-full-1-1-0 | 40.568 | Yes |
| serial-transform-full-2-0-0 | 39.216 | Yes |
| serial-transform-full-2-1-0 | 38.974 | Yes |

Elapsed 246.08 seconds. Charged 6/6 bounds and 86400/86,400 logical steps. The per-bound ceiling remains 120 seconds; only the separately frozen worker allocation is changed.

This is a finite execution check, not a causal concurrency benchmark, a new mathematical bound or an aircraft result. The failed four-worker study and unused-endpoint optimization remain unchanged. Future certificate generation needs a separate finite freeze.

[Frozen scope](PLAN.md) · [Whole-bound profile](../ilvis0-whole-bound-profile/README.md).
