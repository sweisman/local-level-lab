# Retrospective prediction results

**5/6 training fits converged. Prediction comparison: unresolved.** All results below come from the same previously selected recording. The final portion was withheld from these new fits, but the whole recording had already been examined during development. This is a retrospective prediction check, not an independent confirmation or a calibrated statistical detection.

**No upstream removal favors globe** in the completed prediction comparison: the globe family has lower prediction cost than the stationary flat disc.

**Upstream removal allowed remains unresolved.** Stationary flat disc has not converged. Its best permitted fit has not been established; an unfinished fit does not count as equal support for the models.

An IMU (inertial measurement unit) records turning and acceleration. The source is `ILVIS0_applanix_57300_610_LVIS_38614965.013`, IMU type 21, 2015-10-05 12:45:50–12:53:08 UTC, median ground speed 878.1 km/h. Fit the first 292 receiver epochs (291 seconds) and predict the remaining 147 epochs (146 seconds), with one second between portions. The model propagates continuously from its initial state; it receives no GPS reset at the split.

## Direct prediction errors

Direct errors compare the propagated track with the later receiver positions without applying a correlated-error adjustment. Horizontal distance uses the same common reference coordinate metric as the clock trial. Calibration and initialization use training inputs only. Both cases ask whether a fraction of the background rotation was removed before the IMU measurements were logged: one fixes that removal to zero, and the other fits a common fraction. These retain the original processing assumptions.

| Processing case | Model | Fit status | Training horizontal / vertical RMS (m) | Prediction horizontal / vertical RMS (m) | Evaluations |
|---|---|---|---:|---:|---:|
| No upstream removal | Rotating globe | converged | 0.0420821 / 0.137316 | 2.44938 / 3.32878 | 129 |
| No upstream removal | Stationary globe | converged | 25.2562 / 0.547842 | 142.914 / 2.02727 | 126 |
| No upstream removal | Stationary flat disc | converged | 12.9151 / 1.40734 | 165.962 / 3.17364 | 127 |
| Upstream removal allowed | Rotating globe | converged | 0.0424898 / 0.13736 | 2.22229 / 3.3264 | 129 |
| Upstream removal allowed | Stationary globe | converged | 25.2562 / 0.547843 | 142.907 / 2.02736 | 176 |
| Upstream removal allowed | Stationary flat disc | unresolved | 8.4455 / 1.29983 | 255.775 / 2.56144 | 200 |

## Covariance-adjusted diagnostics

These diagnostics condition the assumed receiver errors on the training residuals using the full-window cross-covariance. They do not alter the predicted aircraft track or add GPS fixes to its propagation. Costs remain separate from the direct errors above. Parameter uncertainty is omitted; these are plug-in checks at fitted parameters, not calibrated predictive coverage.

| Processing case | Model | Training cost | Primary prediction cost | Conservative prediction cost, same parameters |
|---|---|---:|---:|---:|
| No upstream removal | Rotating globe | 1.0234 | 23.824 | 0.604954 |
| No upstream removal | Stationary globe | 6237.87 | 46989.3 | 868.638 |
| No upstream removal | Stationary flat disc | 1994.89 | 100565 | 2355.07 |
| Upstream removal allowed | Rotating globe | 1.02304 | 20.5901 | 0.534937 |
| Upstream removal allowed | Stationary globe | 6237.87 | 46984.5 | 868.549 |
| Upstream removal allowed | Stationary flat disc | 1352.61 | 216754 | 4823.18 |

Model ordering is descriptive. Both globe candidates are profiled at the shape stage; the rotation comparison is reported only after all six fits converge and both processing cases favor globe. Unfinished fits are retained as unfinished and are not treated as equally good model fits.

Rotation comparison is withheld because shape is not consistently resolved in favor of globe.

## Evidence and reproduction

The six starts used 887 recorded evaluations and about 40.4 minutes of fitting/diagnostics. An interrupted or failed start remains charged and has no retry allowance. [Fit ledger](fit-comparisons.csv) records stopping messages and gradients; per-epoch compressed CSV files preserve training/prediction roles, direct errors and both innovation streams. [Plan](PLAN.md) records the split, assumptions and finite scope. Original studies remain frozen.

This renderer verifies publication hashes and reads saved metadata only. It performs no native prediction or optimization.

```sh
env PYTHONPATH=analysis ~/venv/bin/python docs/ilvis0-prediction-trial-20261011/build_report.py
```
