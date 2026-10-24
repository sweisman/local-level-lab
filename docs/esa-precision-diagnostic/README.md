# Precision matters in the ESA stopping calculation

**24/24 saved-point diagnostics completed and verified.**

Each row uses the same saved calibration and the same bounded correction.
No calibration was fitted again. The binary64 legacy path reproduces
both original residual vectors exactly. All earlier observations, physical
equations, clock scheduling and acceptance limits remain fixed.

Cost-change values below are in units of **1e-8**, the existing cost-stability
limit. A value below 1 passes this component only; no original fit is reclassified.

| Candidate | Removal | Working errors | Start | Original numerical pass | Legacy | Stable wrap | Extended precision |
|---|---|---|---:|---|---:|---:|---:|
| Globe + field | Zero | Short memory | 0 | No | 4.454 | 4.47 | 0.01213 |
| Globe + field | Zero | Short memory | 1 | No | 7.715 | 7.757 | 0.01191 |
| Globe + field | Zero | Persistent | 0 | Yes | 0.4005 | 0.4582 | 0.002126 |
| Globe + field | Zero | Persistent | 1 | No | 2.973 | 3.207 | 0.07687 |
| Globe + field | Profiled | Short memory | 0 | No | 5.113 | 5.104 | 0.003909 |
| Globe + field | Profiled | Short memory | 1 | No | 5.027 | 5.016 | 0.004172 |
| Globe + field | Profiled | Persistent | 0 | No | 3.832 | 3.904 | 0.08309 |
| Globe + field | Profiled | Persistent | 1 | No | 1.085 | 0.8386 | 0.001414 |
| Globe + zero field | Zero | Short memory | 0 | Yes | 9.402e-05 | 0.0001052 | 0.001179 |
| Globe + zero field | Zero | Short memory | 1 | No | 0.009267 | 0.009286 | 0.00164 |
| Globe + zero field | Zero | Persistent | 0 | Yes | 0.01542 | 0.01536 | 3.695e-05 |
| Globe + zero field | Zero | Persistent | 1 | Yes | 0.0008013 | 0.0007842 | 7.162e-05 |
| Globe + zero field | Profiled | Short memory | 0 | No | 0.007696 | 0.007732 | 0.001045 |
| Globe + zero field | Profiled | Short memory | 1 | Yes | 0.008209 | 0.008224 | 6.908e-05 |
| Globe + zero field | Profiled | Persistent | 0 | No | 0.01071 | 0.01066 | 0.002755 |
| Globe + zero field | Profiled | Persistent | 1 | Yes | 0.01281 | 0.01274 | 4.796e-05 |
| Disc | Zero | Short memory | 0 | No | 0.006661 | 0.006662 | 0.0007469 |
| Disc | Zero | Short memory | 1 | No | 0.007987 | 0.007979 | 0.002217 |
| Disc | Zero | Persistent | 0 | Yes | 0.006213 | 0.006208 | 0.0006108 |
| Disc | Zero | Persistent | 1 | No | 0.000141 | 0.0001176 | 0.0007406 |
| Disc | Profiled | Short memory | 0 | No | 0.008727 | 0.008715 | 0.0005863 |
| Disc | Profiled | Short memory | 1 | No | 0.001807 | 0.001817 | 0.0002648 |
| Disc | Profiled | Persistent | 0 | No | 0.005558 | 0.005557 | 0.0002532 |
| Disc | Profiled | Persistent | 1 | Yes | 0.01174 | 0.01175 | 0.0002203 |

Stable wrapping avoids rounding already-small longitude differences.
Extended precision also reduces rounding accumulated during integration;
receiver coordinates are subtracted before conversion back to binary64.
The packet clock, parameter products and processing-fraction mapping retain
their original binary64 conventions.

These results diagnose precision sensitivity at fixed points. They do not
prove a global optimum, certify a roundoff bound or qualify a revised solver.
The next gate is independent qualification of the wider-precision derivative
and stopping path. All original labels and seven protected confirmation
groups remain unchanged.

The run used 96 value calculations in 1.12 minutes.
The audit uses saved arrays and performs no trajectory propagation.

[Every point and mode](precision.csv) · [Frozen plan](PLAN.md) ·
[Original stopping diagnostic](../esa-stopping-resolution/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
