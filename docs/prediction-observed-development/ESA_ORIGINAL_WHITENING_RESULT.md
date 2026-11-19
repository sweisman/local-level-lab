# Exact cost changes under the original ESA training weights

All three replays reproduced the original training covariance identity
and all 1,200 whitened residual components per model exactly. The
compressed factor snapshots gave the same whitening after restoration.
They can now score additional earlier-period positions without rebuilding
the inertial covariance.

| Model | Allowance | Linear estimate | Exact change in training loss | Within allowance |
|---|---:|---:|---:|---|
| Globe with specified field | 0.001 | 0.001000000 | 0.001000270 | No |
| Globe with specified field | 0.01 | 0.007750181 | 0.007752985 | Yes |
| Globe with zero field | 0.001 | 0.001000000 | 0.001000000297 | No |
| Globe with zero field | 0.01 | 0.010000000 | 0.010000004232 | No |
| Disc with zero field | 0.001 | 0.001000000 | 0.001000005930 | No |
| Disc with zero field | 0.01 | 0.010000000 | 0.009999999413 | Yes |

The largest difference between the linear and exact loss changes was
0.000002804. All four exceedances were less than 0.03% of their allowance.
The specified-field model's larger step reached its parameter cap before
reaching the requested allowance. All six scores were inside the wider
white-covariance bounds reported by the
[earlier-fit cost check](ESA_EARLIER_FIT_COST_RESULT.md).

This verifies the six steps under the original archived error law.
Future exact-budget searches can reuse the factors and leave room for the
linear approximation error. A calibration-region bound for all directions
and an independently supported aircraft error law remain open.

Three tasks passed their replay checks. There were no optimizer starts,
later receiver reads or reserved-flight reads.

[Fixed replay plan](ESA_ORIGINAL_WHITENING_PLAN.md) ·
[How the evidence is stored](../REPRODUCIBILITY.md)

Closed study ID `esa-original-whitening-v1-20261118`. Manifest SHA-256
`41b966cd477a2ac0fa5bf3b950d19523e6909ed2bbbae9bcc91a2addbadf337d`.
Each sealed task contains `training-factors.npz` and
`exact-earlier-cost.json`. The report binds the factor bytes to the
archived training covariance identity.
