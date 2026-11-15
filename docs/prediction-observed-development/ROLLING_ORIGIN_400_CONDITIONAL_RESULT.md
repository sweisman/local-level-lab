# Earlier-origin conditional forecast check

The two fit outcomes and all available early-only conditioning tasks were sealed before the later 120 receiver positions were scored.

| IMU error law | Both steps passed | Raw horizontal RMS (m) | Conditioned horizontal RMS (m) | Conditioned height RMS (m) |
| --- | --- | ---: | ---: | ---: |
| increment | yes | 5.380 | 0.561 | 0.169 |
| point | yes | 5.381 | 0.561 | 0.169 |

Nominal 95% marginal ranges contain the later reports (north 120/120, east 120/120, up 120/120). The normalized errors remain strongly time-correlated (lag-one correlations 0.986–0.999); 120 reports therefore do not constitute 120 independent checks. The two assumed IMU error laws give nearly identical forecasts and this comparison does not choose between them.

The machine-readable result also gives signed errors and covariance details. This one selected development recording does not calibrate coverage or establish physical adequacy; the scientific decision is abstain. Seven reserved flight groups remain unopened.

[Detailed result](ROLLING_ORIGIN_400_CONDITIONAL_RESULT.json).
