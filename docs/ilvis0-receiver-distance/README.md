# How the receiver-error assumptions change trajectory separation

**12/12 saved-data comparisons completed.** These calculations hold every calibration fixed and use earlier predictions only. They create no observations and perform no fits.

The distance below measures separation between two predicted training trajectories relative to a supplied receiver covariance. A larger value means greater separation under that assumption. It is not a p-value, observed likelihood ratio or Earth-model vote.

| Model | Processing case | Correlation time (s) | Distance: 5 epochs | Distance: 289 epochs | Dense north/east/height RMS difference (m) |
|---|---|---:|---:|---:|---|
| Globe + field | Zero removal | 10 | 3.247 | 7.120 | 1.199 / 1.598 / 0.741 |
| Globe + field | Zero removal | 300 | 5.257 | 8.244 | 1.199 / 1.598 / 0.741 |
| Globe + field | Profiled removal | 10 | 3.254 | 7.135 | 1.197 / 1.616 / 0.743 |
| Globe + field | Profiled removal | 300 | 5.244 | 8.269 | 1.197 / 1.616 / 0.743 |
| Globe, zero field | Zero removal | 10 | 3.246 | 7.098 | 1.197 / 1.589 / 0.744 |
| Globe, zero field | Zero removal | 300 | 5.259 | 8.230 | 1.197 / 1.589 / 0.744 |
| Globe, zero field | Profiled removal | 10 | 3.252 | 7.112 | 1.195 / 1.606 / 0.746 |
| Globe, zero field | Profiled removal | 300 | 5.244 | 8.254 | 1.195 / 1.606 / 0.746 |
| Stationary disc | Zero removal | 10 | 3.121 | 4.906 | 1.196 / 0.615 / 0.746 |
| Stationary disc | Zero removal | 300 | 5.065 | 6.381 | 1.196 / 0.615 / 0.746 |
| Stationary disc | Profiled removal | 10 | 3.126 | 4.912 | 1.194 / 0.609 / 0.750 |
| Stationary disc | Profiled removal | 300 | 5.078 | 6.409 | 1.194 / 0.609 / 0.750 |

The table compares the selected low/high pair within each candidate. The evidence also keeps both distances from the original calibration. All cases use the same coordinate conversion, noise scales, shared offset and full-record drift anchor; only correlation time changes.

**This covers the receiver component only.** Accumulated IMU noise, covariance estimation, complete nonlinear calibration uncertainty and numerical/clock treatment remain unqualified. The 53-stretch findings are unchanged, and no new observed prediction fits are authorized.

[Frozen calculation](PLAN.md) · [Saved trajectories](../ilvis0-witness-density/README.md) · [Error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md)
