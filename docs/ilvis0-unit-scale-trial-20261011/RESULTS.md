# Fixed solver scaling: matched prediction comparison

**Comparison qualification: not passed.** Passing requires all six new fits to converge, preserving the five previously completed fits without worsening their training objectives by more than 0.1%. This does not qualify a global optimum, factory calibration or statistical significance. The original unfinished result remains unchanged. [Matched original results](matched-baseline.csv) preserve every comparison.


**5/6 training fits converged. Prediction comparison: unresolved.** All results below come from the same previously selected recording. The final portion was withheld from these new fits, but the whole recording had already been examined during development. This is a retrospective prediction check, not an independent confirmation or a calibrated statistical detection.

**No upstream removal favors globe** in the completed prediction comparison: the globe family has lower prediction cost than the stationary flat disc.

**Upstream removal allowed remains unresolved.** Stationary flat disc has not converged. Its best permitted fit has not been established; an unfinished fit does not count as equal support for the models.

An IMU (inertial measurement unit) records turning and acceleration. The source is `ILVIS0_applanix_57300_610_LVIS_38614965.013`, IMU type 21, 2015-10-05 12:45:50–12:53:08 UTC, median ground speed 878.1 km/h. Fit the first 292 receiver epochs (291 seconds) and predict the remaining 147 epochs (146 seconds), with one second between portions. The model propagates continuously from its initial state; it receives no GPS reset at the split.

## Direct prediction errors

Direct errors compare the propagated track with the later receiver positions without applying a correlated-error adjustment. Horizontal distance uses the same common reference coordinate metric as the clock trial. Calibration and initialization use training inputs only. Both cases ask whether a fraction of the background rotation was removed before the IMU measurements were logged: one fixes that removal to zero, and the other fits a common fraction. These retain the original processing assumptions.

| Processing case | Model | Fit status | Training horizontal / vertical RMS (m) | Prediction horizontal / vertical RMS (m) | Evaluations |
|---|---|---|---:|---:|---:|
| No upstream removal | Rotating globe | converged | 0.0420819 / 0.137315 | 2.44939 / 3.32878 | 106 |
| No upstream removal | Stationary globe | converged | 25.2562 / 0.547846 | 142.896 / 2.0275 | 93 |
| No upstream removal | Stationary flat disc | converged | 12.9151 / 1.40734 | 165.962 / 3.17364 | 148 |
| Upstream removal allowed | Rotating globe | converged | 0.0424884 / 0.137349 | 2.22324 / 3.3264 | 103 |
| Upstream removal allowed | Stationary globe | converged | 25.2562 / 0.547845 | 142.896 / 2.02749 | 99 |
| Upstream removal allowed | Stationary flat disc | unresolved | 8.45319 / 1.32933 | 255.695 / 2.72764 | 200 |

## Covariance-adjusted diagnostics

These diagnostics condition the assumed receiver errors on the training residuals using the full-window cross-covariance. They do not alter the predicted aircraft track or add GPS fixes to its propagation. Costs remain separate from the direct errors above. Parameter uncertainty is omitted; these are plug-in checks at fitted parameters, not calibrated predictive coverage.

| Processing case | Model | Training cost | Primary prediction cost | Conservative prediction cost, same parameters |
|---|---|---:|---:|---:|
| No upstream removal | Rotating globe | 1.0234 | 23.8242 | 0.604959 |
| No upstream removal | Stationary globe | 6237.87 | 46976.3 | 868.4 |
| No upstream removal | Stationary flat disc | 1994.89 | 100565 | 2355.07 |
| Upstream removal allowed | Rotating globe | 1.02304 | 20.6033 | 0.535226 |
| Upstream removal allowed | Stationary globe | 6237.87 | 46976.5 | 868.403 |
| Upstream removal allowed | Stationary flat disc | 1352.28 | 216460 | 4815.96 |

Model ordering is descriptive. Both globe candidates are profiled at the shape stage; the rotation comparison is reported only after all six fits converge and both processing cases favor globe. Unfinished fits are retained as unfinished and are not treated as equally good model fits.

Rotation comparison is withheld because shape is not consistently resolved in favor of globe.

## Evidence and reproduction

The six starts used 749 recorded evaluations and about 33.4 minutes of fitting/diagnostics. An interrupted or failed start remains charged and has no retry allowance. [Fit ledger](fit-comparisons.csv) records stopping messages and gradients; per-epoch compressed CSV files preserve training/prediction roles, direct errors and both innovation streams. [Plan](PLAN.md) records the split, assumptions and finite scope. Original studies remain frozen.

This renderer verifies publication hashes and reads saved metadata only. It performs no native prediction or optimization.

```sh
env PYTHONPATH=analysis ~/venv/bin/python docs/ilvis0-unit-scale-trial-20261011/build_report.py
```
