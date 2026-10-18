# Diagnosis of the generated height-only endpoint

Completed **33 fixed-point evaluations**, zero optimizer starts and zero original-recording reads. The saved failure reproduced deterministically; its label is unchanged.

| Proposed correction | Fraction | Linear cost | Actual cost | Fresh stationarity | Largest retained prediction change (m) |
|---|---:|---:|---:|---:|---:|
| unscaled | 1.0 | 1.67208e-12 | 0.0235453 | 0.153445 | 0.000674488 |
| unscaled | 0.25 | 1.11655e-08 | 9.64133e-05 | 0.00981903 | 4.24831e-05 |
| unscaled | 0.0625 | 1.74453e-08 | 5.49203e-07 | 0.000741079 | 2.63361e-06 |
| column_scaled | 1.0 | 1.67208e-12 | 0.0235453 | 0.153445 | 0.000674488 |
| column_scaled | 0.25 | 1.11655e-08 | 9.64133e-05 | 0.00981903 | 4.24831e-05 |
| column_scaled | 0.0625 | 1.74453e-08 | 5.49203e-07 | 0.000741079 | 2.63361e-06 |

These are proposals from the same saved point, not optimization trajectories or new converged fits. No archive result or qualification gate changed.

[Fixed scope](PLAN.md) · [Prior qualification](../ilvis0-projected-fitting-controls-20261018/README.md).
