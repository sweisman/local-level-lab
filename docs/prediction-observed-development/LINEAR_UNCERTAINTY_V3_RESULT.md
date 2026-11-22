# Fitted calibration uncertainty does not explain the ESA height miss

The corrected one-task study completed. It generated the missing native
forecast derivative at the saved fit and verified that all 1,200 generated
positions **exactly match** the sealed forecast. All 26 whitened training
Jacobian columns replay the saved fit within the fixed tolerances. The
training rank is 26/26, and the local parameter step remains inside the
original bounds. Its largest normalized correction is about 1.7 × 10⁻⁸,
so the predicted path barely changes.

| Later GPS check, 400 reports | Fixed parameters | Local fitted-parameter uncertainty added |
|---|---:|---:|
| Horizontal prediction RMS | 2.849 m | 2.849 m |
| Height prediction RMS | 11.881 m | 11.881 m |
| Height reports inside nominal 95% marginal interval | 25/400 | **26/400** |
| Reports inside nominal 95% three-axis region | 37/400 | **40/400** |
| Largest predicted height standard deviation | 3.556 m | 6.495 m |

The local covariance grows, but the persistent height error remains far
outside it. This rules out **the omitted local linear parameter variance alone**
as an explanation under the declared error law. It does not rule out nonlinear
calibration uncertainty, another error law, timing or processing effects, or
a mismatch in the physical observation model.

The [machine report](linear-uncertainty-v3-result.json) verifies the sealed
study, forecast and original later receiver rows. This one segment's reports
are strongly correlated, so 26/400 is descriptive, not a binomial coverage
estimate. The run used one thread and completed in 366 seconds. The
[original plan](LINEAR_UNCERTAINTY_V3_PLAN.md) and two preserved technical
failures record the full sequence. No reserved ESA group was opened.
The observed error law and uncertainty coverage remain **unqualified**; the
scientific decision is **abstain**.
