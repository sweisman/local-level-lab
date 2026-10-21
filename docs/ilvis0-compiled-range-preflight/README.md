# Actual-baseline transport preflight

6/6 source/reference comparisons passed.

| Candidate / removal | Matched | Old N / E / height allowance (m) | Fresh allowance (m) | Retained minimum (m) |
|---|---|---:|---:|---:|
| Globe with specified field / zero | Yes | 0.171107 / 0.227968 / 0.173645 | 0.147082 / 0.220162 / 0.155035 | 0.147082 / 0.220162 / 0.155035 |
| Globe with specified field / profiled | Yes | 0.19008 / 0.244045 / 0.192634 | 0.166111 / 0.235711 / 0.174084 | 0.166111 / 0.235711 / 0.174084 |
| Globe with zero field / zero | Yes | 0.116459 / 0.125147 / 0.114864 | 0.103554 / 0.11208 / 0.108039 | 0.103554 / 0.11208 / 0.108039 |
| Globe with zero field / profiled | Yes | 0.150419 / 0.161838 / 0.148849 | 0.136653 / 0.14828 / 0.141221 | 0.136653 / 0.14828 / 0.141221 |
| Flat disc / zero | Yes | 0.0770756 / 0.0266839 / 0.0767491 | 0.0734974 / 0.0261504 / 0.0711165 | 0.0734974 / 0.0261504 / 0.0711165 |
| Flat disc / profiled | Yes | 0.116663 / 0.039157 / 0.116332 | 0.112378 / 0.0385321 / 0.10999 | 0.112378 / 0.0385321 / 0.10999 |

Charged 6/6 bounds and 19200/19,200 bound packet-steps. Elapsed 244.00 seconds. Preserved 36/36 exact support verifications.

This measures native unshared error allowances on the actual saved source domains. It does not recompute complete sector unions or qualify a future-range target. The tighter norm-constrained body-source interval is not installed. No native trajectory, LP, aircraft observation, protected ESA data or optimizer was used.

[Frozen scope](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
