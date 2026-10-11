# What grows when GPS fitting stops?

**The rotating-globe track remains much closer horizontally during prediction, but its errors grow after GPS fitting stops.** Five of six training fits converged. The flat-disc fit with removal allowed exhausted its allowance, so the full two-case comparison remains unresolved.

An IMU (inertial measurement unit) records turning and acceleration. This audit uses saved results from one IMU-type-21 recording, `ILVIS0_applanix_57300_610_LVIS_38614965.013`, on 2015-10-05. The stretch lasts 7.30 minutes at median ground speed 878.1 km/h. The first 4.85 minutes supplied GPS fitting positions; the final 2.43 minutes were propagated without GPS resets. This recording was examined earlier, so the test is retrospective development, not independent confirmation.

## Error growth

These are direct distances to the recorded receiver positions. The endpoint column describes the final instant; RMS describes the entire prediction portion. Vertical endpoint error retains its sign.

| Processing | Model | Status | Training H / V RMS (m) | Prediction H / V RMS (m) | Final H / signed V (m) |
|---|---|---|---:|---:|---:|
| No removal | Rotating globe | converged | 0.042 / 0.137 | 2.449 / 3.329 | 5.409 / 7.324 |
| No removal | Still globe | converged | 25.256 / 0.548 | 142.914 / 2.027 | 266.325 / 5.296 |
| No removal | Flat disc | converged | 12.915 / 1.407 | 165.962 / 3.174 | 385.662 / 3.388 |
| Removal allowed | Rotating globe | converged | 0.042 / 0.137 | 2.222 / 3.326 | 4.921 / 7.318 |
| Removal allowed | Still globe | converged | 25.256 / 0.548 | 142.907 / 2.027 | 266.311 / 5.297 |
| Removal allowed | Flat disc | unresolved | 8.446 / 1.300 | 255.775 / 2.561 | 572.492 / -7.954 |

[Thirty-second prediction sections](error-growth.csv) show where errors accumulate at the same fixed parameters. They are not refits or independent trials.

| Processing | Seconds after prediction begins | Rotating-globe H / V RMS (m) |
|---|---:|---:|
| No removal | 0–29 | 0.152 / 0.387 |
| No removal | 30–59 | 0.690 / 1.117 |
| No removal | 60–89 | 1.638 / 2.237 |
| No removal | 90–119 | 2.881 / 3.858 |
| No removal | 120–146 | 4.462 / 6.056 |
| Removal allowed | 0–29 | 0.135 / 0.387 |
| Removal allowed | 30–59 | 0.615 / 1.116 |
| Removal allowed | 60–89 | 1.480 / 2.236 |
| Removal allowed | 90–119 | 2.618 / 3.855 |
| Removal allowed | 120–146 | 4.049 / 6.052 |

## Calibration changes with the fitting window

This compares earlier whole-stretch header-clock fits with the new training-only fits. Bounds and processing assumptions are matched, but the observations fitted differ. Parameter movements show readjustment; they do not establish its cause or measure factory calibration.

| Processing | Model | Parameters at limits: full / training | Jacobian condition ratio | Stationarity / limit |
|---|---|---:|---:|---:|
| No removal | Rotating globe | 2 / 3 | 2.232e+07 | 0.004974 |
| No removal | Still globe | 14 / 15 | 1.925e+07 | 0.00124 |
| No removal | Flat disc | 15 / 14 | 6.994e+07 | 8.701e-07 |
| Removal allowed | Rotating globe | 3 / 3 | 3.226e+07 | 0.0103 |
| Removal allowed | Still globe | 15 / 16 | 2.294e+07 | 0.0005328 |
| Removal allowed | Flat disc | 15 / 13 | 5.161e+07 | 39.59 |

The condition ratio uses the saved Jacobian’s largest and smallest singular values in normalized parameter coordinates. It is not a confidence interval or a unique diagnosis. Converged fits can also have large ratios. The original prediction fitter did not save Jacobian vectors, gradient components or iteration history, so this audit cannot identify which parameter caused the unfinished fit.

| Processing | Rotating-globe parameter | Unit | Full-window value | Training value | Full / training limit |
|---|---|---|---:|---:|---|
| No removal | gyro_bias_z | deg/hour | 1 | 1 | upper / upper |
| No removal | accel_bias_z | m/s2 | 0.0310887 | -0.0242855 | interior / interior |
| No removal | gyro_gain_z | % | -2 | 2 | lower / upper |
| No removal | gravity_delta | m/s2 | -0.00839876 | -0.05 | interior / lower |
| No removal | time_offset | s | 0.00898592 | -0.0241677 | interior / interior |
| Removal allowed | gyro_bias_z | deg/hour | 1 | 1 | upper / upper |
| Removal allowed | accel_bias_z | m/s2 | 0.0325003 | -0.0245013 | interior / interior |
| Removal allowed | gyro_gain_z | % | -2 | 2 | lower / upper |
| Removal allowed | gravity_delta | m/s2 | -0.00995147 | -0.0499997 | interior / lower |
| Removal allowed | time_offset | s | 0.00905022 | -0.0245396 | interior / interior |

**Z gyro gain flips from −2% in the whole-stretch fits to +2% in the training-only fits under both processing cases.** The estimated constant Z offset stays at +1°/hour, and gravity correction returns to its lower limit. These shifts demonstrate sensitivity to the fitting window; they do not prove that the instrument calibration changed during the flight. Completing the solver alone will not settle this calibration question.

[All parameter changes](parameter-changes.csv) preserve signed limits and units. The [fit ledger](fit-diagnostics.csv) preserves stopping messages and stationarity checks, including the unfinished flat fit.

## What to do next

Test a solver alternative on independently known optima before any new observed fits. Keep the physical models, bounds, covariance, split and initialization unchanged in a separately frozen matched comparison. Save accepted-step history, fresh gradient components and weak parameter directions. Neither increasing the old allowance nor relabeling its failure is authorized. See the [solver and replication plan](NEXT_PLAN.md).

This audit verifies published hashes, matched fits and per-epoch RMS. It makes **zero optimizer starts and zero native predictions**. It cannot calibrate statistical significance or attribute the retained rotation field’s physical cause.

```sh
env PYTHONPATH=analysis ~/venv/bin/python docs/ilvis0-prediction-audit-20261011/build_report.py
```
