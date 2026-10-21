# Where the source calculation spends its time

6/6 original source profiles completed. Elapsed 73.99 seconds.

| Candidate / processing | Prefixes | Physical values | Derivative intervals | Direct remainder |
|---|---:|---:|---:|---:|
| Specified-field globe / zero | 1471/1471 | 25.406 s | 2.625 s | 12.551 s |
| Specified-field globe / profiled | 1471/1471 | 25.582 s | 2.614 s | 12.683 s |
| Zero-field globe / zero | 1471/1471 | 25.889 s | 2.660 s | 12.837 s |
| Zero-field globe / profiled | 1471/1471 | 26.029 s | 2.633 s | 12.959 s |
| Flat disc / zero | 1471/1471 | 16.477 s | 1.677 s | 8.198 s |
| Flat disc / profiled | 1471/1471 | 16.471 s | 1.687 s | 8.205 s |

Profiler overhead is included. These timings cover only source streams, not full prediction bounds. Both original phase certificates and endpoint rotation state remain. No optimization is qualified by these timings.

Charged 6/6 source profiles and 28800/28,800 logical source steps; unused reserved work remains charged. No full native trajectory, LP, optimizer or original-aircraft read ran.

[Frozen scope](PLAN.md) · [Remaining width](../ilvis0-east-width-audit/INTERPRETATION.md).
