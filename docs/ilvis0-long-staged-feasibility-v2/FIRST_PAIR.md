# First pair: completed checks, unusably wide ranges

Both specified-field cases completed their numerical checks and retained the known answer. Neither meets the frozen prediction-width target. This fixed audit covers only those first two cases; see the [study page](README.md) for the full study status.

| Processing | North width | East width | Height width | Target N / E / height |
|---|---:|---:|---:|---:|
| Zero removal | 2,026.6 km | 2,413.3 km | 1,462.7 km | 20 / 20 / 50 m |
| Profiled removal | 2,024.5 km | 2,418.7 km | 1,461.0 km | 20 / 20 / 50 m |

The additive, unshared approximation allowance accounts for 87.4%–90.7% of these reported widths. Training reduces the initial-acceleration change bound from about 24.4 m/s² to 1.7 m/s², but the later training stage hardly improves it. The remaining long-history approximation is still much too loose.

**These are generated-data bounds, not measured aircraft errors.** They do not change the 53-stretch model comparisons or measure instrument drift. Containing the known answer does not qualify an interval thousands of kilometres wide.

The next method must sharpen the long-history enclosure and its use of training information. The five-epoch training subset also does not establish what all 292 earlier training epochs could achieve. More optimizer evaluations, a larger error allowance or a wider success threshold would not resolve this test.

All 158 side artifacts of these two cases were checked against their seals. This read-only audit performs no integration, fitting or active-shard merge. It is a first-pair diagnosis, not the final six-case study summary.

[Frozen scope](PLAN.md) · [Remaining gates](V01_GATES.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
