# Actual-baseline transport preflight

2/6 source/reference comparisons passed.

| Candidate / removal | Matched | Best saved N / E / height allowance (m) | Fresh allowance (m) | Retained minimum (m) |
|---|---|---:|---:|---:|
| Globe with specified field / zero | No | unavailable | unavailable | unavailable |
| Globe with specified field / profiled | No | unavailable | unavailable | unavailable |
| Globe with zero field / zero | No | unavailable | unavailable | unavailable |
| Globe with zero field / profiled | No | unavailable | unavailable | unavailable |
| Flat disc / zero | Yes | 0.0734974 / 0.0261504 / 0.0711165 | 0.14863 / 0.0482135 / 0.0503863 | 0.0734974 / 0.0261504 / 0.0503863 |
| Flat disc / profiled | Yes | 0.112378 / 0.0385321 / 0.10999 | 0.167598 / 0.0556985 / 0.069376 | 0.112378 / 0.0385321 / 0.069376 |

Charged 6/6 bounds and 38400/38,400 world/source packet-steps. Elapsed 230.13 seconds. Preserved 36/36 exact support verifications.

Reserved 9,600/9,600 compiled source steps and 9,600/9,600 rounded body bounds separately from full trajectory evaluations.

This measures native unshared error allowances on the actual saved source domains. It does not recompute complete sector unions or qualify a future-range target. The qualified rounded body-source interval is installed. No full trajectory oracle, LP, aircraft observation, protected ESA data or optimizer was used.

[Frozen scope](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
