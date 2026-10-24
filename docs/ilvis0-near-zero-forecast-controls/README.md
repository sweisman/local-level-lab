# Training-only forecast controls

**24/24 fits passed the complete software checks.** The procedure qualified on these controls.

24/24 saved fits passed the numerical stopping checks. The run charged 2,976 native calculations.

No aircraft observations were used. These are short generated tracks with known answers, not Earth-model detections or calibrated confidence intervals.

Small forecast errors do not qualify a failed stopping check.

| Model | Removal profiled | Clock | Start | Stopping check | Largest later axis RMS (mm) |
|---|---|---|---:|---|---:|
| Globe + field | False | header_elapsed | 0 | Passed | 0.000646697 |
| Globe + field | False | header_elapsed | 1 | Passed | 0.00156194 |
| Globe + field | False | nominal_200Hz | 0 | Passed | 0.00359475 |
| Globe + field | False | nominal_200Hz | 1 | Passed | 0.000282559 |
| Globe + field | True | header_elapsed | 0 | Passed | 5.57074e-05 |
| Globe + field | True | header_elapsed | 1 | Passed | 0.000792647 |
| Globe + field | True | nominal_200Hz | 0 | Passed | 0.000237222 |
| Globe + field | True | nominal_200Hz | 1 | Passed | 0.000373246 |
| Globe, zero field | False | header_elapsed | 0 | Passed | 0.000120341 |
| Globe, zero field | False | header_elapsed | 1 | Passed | 3.84911e-05 |
| Globe, zero field | False | nominal_200Hz | 0 | Passed | 0.000138332 |
| Globe, zero field | False | nominal_200Hz | 1 | Passed | 0.000201485 |
| Globe, zero field | True | header_elapsed | 0 | Passed | 1.70241e-05 |
| Globe, zero field | True | header_elapsed | 1 | Passed | 7.84501e-05 |
| Globe, zero field | True | nominal_200Hz | 0 | Passed | 2.56132e-05 |
| Globe, zero field | True | nominal_200Hz | 1 | Passed | 7.13027e-05 |
| Stationary disc | False | header_elapsed | 0 | Passed | 1.62878e-05 |
| Stationary disc | False | header_elapsed | 1 | Passed | 3.65207e-06 |
| Stationary disc | False | nominal_200Hz | 0 | Passed | 9.44334e-06 |
| Stationary disc | False | nominal_200Hz | 1 | Passed | 3.90644e-06 |
| Stationary disc | True | header_elapsed | 0 | Passed | 1.50108e-06 |
| Stationary disc | True | header_elapsed | 1 | Passed | 2.48797e-06 |
| Stationary disc | True | nominal_200Hz | 0 | Passed | 0.000213731 |
| Stationary disc | True | nominal_200Hz | 1 | Passed | 0.000226493 |

The saved audit also compares both starts on each identical track. Forecast differences describe numerical sensitivity; they are not uncertainty bounds. Failures remain unchanged and this completed allowance cannot be restarted.

[Frozen question and limits](PLAN.md) · [Pilot inventory](../ilvis0-prediction-pilot-preparation/README.md) · [Prediction protocol](../PREDICTION_VALIDATION.md)
