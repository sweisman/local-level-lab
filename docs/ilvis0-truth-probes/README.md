# Ambiguity under the original long-study observations

**4/4 numerical tasks complete; 6/12 calibrations meet the actual training constraints.**

These cases use the original nonzero truth and stored perturbed observations, not the earlier zero-reference fixture. Every candidate is checked at all five original training times before its later displacement is interpreted.

| Processing | Feasible calibrations | Sampled N spread | Sampled E spread | Sampled height spread |
|---|---:|---:|---:|---:|
| Zero removal | 4/6 | 13.328 m | 5.365 m | 0.642 m |
| Profiled removal | 2/6 | 5.898 m | 6.049 m | 0.128 m |

Spreads include the known truth. They are sampled numerical separations, not outer uncertainty bounds. The original width targets remain 20/20/50 m. A small sampled spread does not establish those targets over the whole domain.

| Processing | North objective | Scale | Training maximum | Future N / E / height change | Feasible |
|---|---|---:|---:|---|---|
| Zero | Negative | 1/50 | 0.297 m | -2.731 / 0.585 / 0.158 m | Yes |
| Zero | Negative | 1/20 | 0.868 m | -7.074 / 0.051 / 0.585 m | Yes |
| Zero | Negative | 1/10 | 4.106 m | -14.984 / -4.574 / 1.799 m | No |
| Zero | Positive | 1/50 | 0.337 m | 2.599 / -1.342 / -0.056 m | Yes |
| Zero | Positive | 1/20 | 0.776 m | 6.254 / -4.780 / 0.052 m | Yes |
| Zero | Positive | 1/10 | 3.968 m | 11.701 / -14.342 / 0.750 m | No |
| Profiled | Negative | 1/50 | 0.326 m | -2.636 / 2.545 / 0.128 m | Yes |
| Profiled | Negative | 1/20 | 1.155 m | -5.426 / 4.567 / 0.629 m | No |
| Profiled | Negative | 1/10 | 5.260 m | -7.018 / 3.163 / 2.280 m | No |
| Profiled | Positive | 1/50 | 0.355 m | 3.263 / -3.505 / 0.039 m | Yes |
| Profiled | Positive | 1/20 | 1.059 m | 9.344 / -10.565 / 0.411 m | No |
| Profiled | Positive | 1/10 | 5.092 m | 22.692 / -27.158 / 1.880 m | No |

All points are saved before new outcomes. LP feasibility is only a proposal check; the nonlinear predictions determine the reported training label. Every scale is retained, including failures. No candidate causes a retry, a changed limit or an update to the running study.

There are no new aircraft fits or original-data reads. These results do not establish native floating-point execution error, an aircraft error law, statistical significance or a change to the 53-stretch findings.

[Frozen limits](PLAN.md) · [Earlier zero-reference diagnostic](../ilvis0-ray-probes/INTERPRETATION.md) · [Prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md).
