# Long-history reuse comparison

Six fixed generated histories test whether reusing earlier calculations preserves the complete prediction bounds. These are software controls, not aircraft fits. Queries are at 290 and 438 seconds.

| Candidate | Processing | Result | Cold 290 s (s) | Batched two queries (s) | Peak memory (MiB) |
|---|---|---|---:|---:|---:|
| Globe + field | Zero removal | Reference saved; comparison stopped | 0.0 | — | 156.4 |
| Globe + field | Profiled removal | Reference saved; comparison stopped | 0.0 | — | 157.2 |
| Stationary disc | Zero removal | Reference saved; comparison stopped | 3622.0 | — | 382.8 |
| Stationary disc | Profiled removal | Reference saved; comparison stopped | 3621.3 | — | 382.3 |
| Globe, zero field | Zero removal | Reference saved; comparison stopped | 0.0 | — | 386.6 |
| Globe, zero field | Profiled removal | Reference saved; comparison stopped | 0.0 | — | 386.7 |

**Long-history reuse is not qualified.**

The original 438-second results are reused only after checking their inputs, proof, source code, numerical dependencies, compiler and environment. A fresh original calculation at 290 seconds uses the same final conditioning proof. Complete reports and all 51 coefficient columns must agree.

Historical elapsed times are not a controlled same-run speed benchmark. Packet-work counts and actual peak memory are reported separately. No uncertainty target, physical bound or flight selection changes to obtain a pass. Whole-record prediction uncertainty remains a separate gate.

[Frozen scope](PLAN.md) · [Short controls](../ilvis0-native-prefix-controls/README.md) · [Prediction gates](../ilvis0-joint-projection-controls/NEXT_PLAN.md)

## Saved-output audit

All six histories finished. 8 retained original/cached report pairs match exactly; all 12 saved independent point checks pass the unchanged arithmetic allowance. 4 later cached reports were not saved after the tuple/list comparison stopped their tasks. Both disc histories already retain every report.

These saved checks preserve the original failure labels. A separately bounded [recovery](../ilvis0-native-prefix-format-recovery/README.md) reuses all original and point records and calculates only the missing cached outputs. Its numerical repair passed 45 regression checks.
