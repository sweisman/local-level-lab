# Full-history source derivative comparison

6/6 source/reference comparisons passed.

| Candidate / removal | Matched | Best saved N / E / height allowance (m) | Fresh allowance (m) | Retained minimum (m) |
|---|---|---:|---:|---:|
| Globe with specified field / zero | Yes | 0.147082 / 0.220162 / 0.128954 | 0.146899 / 0.223764 / 0.128915 | 0.146899 / 0.220162 / 0.128915 |
| Globe with specified field / profiled | Yes | 0.166111 / 0.235711 / 0.134104 | 0.151845 / 0.222559 / 0.134071 | 0.151845 / 0.222559 / 0.134071 |
| Globe with zero field / zero | Yes | 0.103554 / 0.11208 / 0.0857885 | 0.107479 / 0.114236 / 0.0857742 | 0.103554 / 0.11208 / 0.0857742 |
| Globe with zero field / profiled | Yes | 0.136653 / 0.14828 / 0.101661 | 0.123268 / 0.13491 / 0.101643 | 0.123268 / 0.13491 / 0.101643 |
| Flat disc / zero | Yes | 0.0734974 / 0.0261504 / 0.0503863 | 0.0812865 / 0.0284826 / 0.0503862 | 0.0734974 / 0.0261504 / 0.0503862 |
| Flat disc / profiled | Yes | 0.112378 / 0.0385321 / 0.069376 | 0.100248 / 0.0358317 / 0.06937 | 0.100248 / 0.0358317 / 0.06937 |

Charged 6/6 bounds and 76800/76,800 world/source/derivative packet-steps. Elapsed 161.74 seconds. Preserved 36/36 exact support verifications.

Reserved 9,600/9,600 compiled source steps and 9,600/9,600 rounded body bounds separately from full trajectory evaluations.

This measures native unshared error allowances on the actual saved source domains. It does not recompute complete sector unions or qualify a future-range target. The qualified rounded body-source interval is installed. No full trajectory oracle, LP, aircraft observation, protected ESA data or optimizer was used.

[Frozen scope](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
