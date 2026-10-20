# Streaming native integration

44/48 generated controls passed; study state: terminal.

This study compares chunked integration with the unchanged whole-array kernels, checks independent constant-pose inputs, and measures bounded-block memory/runtime. It performs no archive fits or protected ESA evaluation.

| Control family | Completed | Passed |
|---|---:|---:|
| equivalence | 24 | 24 |
| pose | 18 | 18 |
| scaling | 3 | 2 |

| Scaling mode | Packets | Duration | Runtime | Traced peak memory | State |
|---|---:|---:|---:|---:|---:|
| Value only | 30,000 | 100.0 s | 0.53 s | 0.193 MiB | 560 bytes |
| 27-column tangent | 30,000 | 100.0 s | 1.03 s | 0.234 MiB | 14,168 bytes |
| Value only | 120,000 | 400.0 s | 2.06 s | 0.339 MiB | 560 bytes |

Traced memory includes generated block arrays and query results, but excludes the compiler and shared-library code. No complete long-record array is constructed in the scaling stage. The native loops are serial; four numerical threads are reserved as a ceiling, not four-way speedup.

Charged 886 native calls and 378,936 packet visits in 18.97 seconds.

Passing these controls establishes software equivalence on the declared generated cases. It does not establish calibrated uncertainty, actual recording continuity, predictive adequacy or an eight-hour fit runtime. The recording-scale uncertainty bounds remain too wide; new observed prediction fits remain blocked.

[Frozen method and acceptance](PLAN.md) · [Technical roadmap](../ANALYSIS_ROADMAP.md) · [Next analyses](../NEXT_STEPS.md).
