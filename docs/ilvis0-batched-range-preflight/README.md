# Full-history batched source comparison

6/6 source/reference comparisons passed.

| Candidate / removal | Matched | Best saved N / E / height allowance (m) | Fresh allowance (m) | Retained minimum (m) |
|---|---|---:|---:|---:|
| Globe with specified field / zero | Yes | 0.147082 / 0.220162 / 0.155035 | 0.214633 / 0.291678 / 0.128954 | 0.147082 / 0.220162 / 0.128954 |
| Globe with specified field / profiled | Yes | 0.166111 / 0.235711 / 0.174084 | 0.219576 / 0.289997 / 0.134104 | 0.166111 / 0.235711 / 0.134104 |
| Globe with zero field / zero | Yes | 0.103554 / 0.11208 / 0.108039 | 0.175172 / 0.181158 / 0.0857885 | 0.103554 / 0.11208 / 0.0857885 |
| Globe with zero field / profiled | Yes | 0.136653 / 0.14828 / 0.141221 | 0.190971 / 0.202129 / 0.101661 | 0.136653 / 0.14828 / 0.101661 |
| Flat disc / zero | Yes | 0.0734974 / 0.0261504 / 0.0711165 | 0.14863 / 0.0482135 / 0.0503863 | 0.0734974 / 0.0261504 / 0.0503863 |
| Flat disc / profiled | Yes | 0.112378 / 0.0385321 / 0.10999 | 0.167598 / 0.0556985 / 0.069376 | 0.112378 / 0.0385321 / 0.069376 |

Charged 6/6 bounds and 38400/38,400 world/source packet-steps. Elapsed 134.46 seconds. Preserved 36/36 exact support verifications.

Reserved 9,600/9,600 compiled source steps and 9,600/9,600 rounded body bounds separately from full trajectory evaluations.

This measures native unshared error allowances on the actual saved source domains. It does not recompute complete sector unions or qualify a future-range target. The qualified rounded body-source interval is installed. No full trajectory oracle, LP, aircraft observation, protected ESA data or optimizer was used.

[Frozen scope](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
