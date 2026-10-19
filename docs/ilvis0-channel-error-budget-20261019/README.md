# Channel error-budget diagnostic

Completed **46/46 diagnostic identities** in 2.11 seconds. Implementation checks passed for 46/46. No original measurements, native integrations or observed fits were used.

Of 108 candidate/trajectory checks, 99 pass the local-linearity screen and 90 pass the trajectory-truncation screen; 81 pass both. These are assumed-error development screens, not scientific detections or calibrated coverage.

[All candidate results](trajectory-candidates.csv) retain every model and window. Noise levels are declared control assumptions, not measured receiver performance. No window is selected from these results.

## Acceleration averaging

| Rotation in one second (degrees) | Mean-packet loss (m/s²) | Summed-vector loss (m/s²) |
|---:|---:|---:|
| 0 | 0 | 8.8817842e-15 |
| 0.1 | 3.1127101e-11 | 1.2451237e-06 |
| 1 | 3.1128096e-09 | 0.0001245119 |
| 5 | 7.782023e-08 | 0.003112513 |
| 20 | 1.2451237e-06 | 0.049729146 |
| 90 | 2.5213736e-05 | 0.97789694 |

These exact rotating-force integrals show that averaging body vectors and averaging their magnitudes are different operations. Neither becomes an exact instantaneous force without a timing/averaging model.

## Noise bias in magnitudes

| Assumed isotropic noise σ (m/s²) | Magnitude bias (m/s²) | Small-noise prediction (m/s²) |
|---:|---:|---:|
| 0.001 | 1.019368e-07 | 1.019368e-07 |
| 0.01 | 1.019368e-05 | 1.019368e-05 |
| 0.1 | 0.001019368 | 0.001019368 |
| 0.5 | 0.0254842 | 0.0254842 |

Averaging more magnitudes does not remove this nonlinear mean shift. Actual noise, calibration, quantization and correlation still need an observational model.

The main 53-stretch findings and the earlier unresolved height-removal sensitivity result are unchanged. These controls do not qualify a new recorded-data likelihood.

[Frozen matrix and limits](PLAN.md) · [Next gate](NEXT_PLAN.md) · [Measurement contributions](../ilvis0-measurement-contribution/README.md).
