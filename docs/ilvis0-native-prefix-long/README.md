# Long-history reuse comparison

Six fixed generated histories test whether reusing earlier calculations preserves the complete prediction bounds. These are software controls, not aircraft fits. Queries are at 290 and 438 seconds.

| Candidate | Processing | Result | Cold 290 s (s) | Batched two queries (s) | Peak memory (MiB) |
|---|---|---|---:|---:|---:|
| Globe + field | Zero removal | Reference saved; comparison stopped | 3736.7 | — | 383.5 |
| Globe + field | Profiled removal | Reference saved; comparison stopped | 3700.9 | — | 383.2 |
| Globe, zero field | Zero removal | Reference saved; comparison stopped | 3724.2 | — | 383.0 |
| Globe, zero field | Profiled removal | Reference saved; comparison stopped | 3741.8 | — | 382.7 |
| Stationary disc | Zero removal | Not started | — | — | — |
| Stationary disc | Profiled removal | Not started | — | — | — |

**Long-history reuse is not qualified.**

The original 438-second results are reused only after checking their inputs, proof, source code, numerical dependencies, compiler and environment. A fresh original calculation at 290 seconds uses the same final conditioning proof. Complete reports and all 51 coefficient columns must agree.

Historical elapsed times are not a controlled same-run speed benchmark. Packet-work counts and actual peak memory are reported separately. No uncertainty target, physical bound or flight selection changes to obtain a pass. Whole-record prediction uncertainty remains a separate gate.

[Frozen scope](PLAN.md) · [Short controls](../ilvis0-native-prefix-controls/README.md) · [Prediction gates](../ilvis0-joint-projection-controls/NEXT_PLAN.md)
