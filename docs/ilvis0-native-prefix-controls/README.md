# Complete native-prefix software comparison

This checks the complete cached state: geographic motion, relative attitudes, accumulated force, common clock, source streams and calibration proof. The reference is the sealed original cold orchestration, with all dependencies fixed by the new study. Inputs are generated software cases, not aircraft recordings.

| Candidate | Processing | Proof | Complete reports equal | Native center error (m) | Prefix + tail steps |
|---|---|---|---|---:|---:|
| Globe + field | Zero removal | physical | Yes | 2.83e-09 | 20 |
| Globe + field | Zero removal | conditioned | Yes | 2.83e-09 | 20 |
| Globe + field | Profiled removal | physical | Yes | 2.83e-09 | 20 |
| Globe + field | Profiled removal | conditioned | Yes | 2.83e-09 | 20 |
| Globe, zero field | Zero removal | physical | Yes | 1.41e-09 | 20 |
| Globe, zero field | Zero removal | conditioned | Yes | 1.41e-09 | 20 |
| Globe, zero field | Profiled removal | physical | Yes | 2.83e-09 | 20 |
| Globe, zero field | Profiled removal | conditioned | Yes | 2.83e-09 | 20 |
| Stationary disc | Zero removal | physical | Yes | 2.83e-09 | 20 |
| Stationary disc | Zero removal | conditioned | Yes | 2.83e-09 | 20 |
| Stationary disc | Profiled removal | physical | Yes | 7.07e-10 | 20 |
| Stationary disc | Profiled removal | conditioned | Yes | 7.07e-10 | 20 |
| Globe + field | Zero removal | physical | Unsupported source rejected by both paths | — | 0 |
| Globe + field | Zero removal | conditioned | Unsupported source rejected by both paths | — | 0 |

Each supported case compares three complete reports and all 51 design columns: 27 physical parameters plus 24 shared source coordinates. An independent native point query checks each center at the predeclared ten-micrometre software allowance. Both physical-domain and training-conditioned proof paths are covered. The latter uses a declared generated acceleration constraint; it is not an observation from a flight.

Two additional controls retain a broader initial-source fixture that the original engine cannot certify. Both paths must reject it with the same insufficient-cap error; it does not become a supported case or disappear from the report.

The common-clock force certificate is still computed by the original cold routine for each query. Cached source work must preserve packet positions, allowances and exact boundary handling. Local tests separately cover zero time and adjacent exact boundaries.

**Long-history performance and full prediction uncertainty remain unqualified.** Passing these short controls is not an aircraft result or a reason to change the 53-stretch findings. A separately bounded long comparison must precede complete-cadence use.

[Frozen scope](PLAN.md) · [Implementation plan](../ilvis0-prefix-reuse/NATIVE_PLAN.md) · [Prediction gates](../ilvis0-joint-projection-controls/NEXT_PLAN.md)
