# Earlier-origin conditional forecast check

Both fits and all permitted conditioning tasks sealed before receiver reports 200–319 were scored.

| IMU error law | Both steps passed | Raw horizontal RMS (m) | Conditioned horizontal RMS (m) | Conditioned height RMS (m) |
|---|---|---:|---:|---:|
| increment | yes | 0.352 | 0.467 | 0.240 |
| point | yes | 0.352 | 0.467 | 0.240 |

Nominal 95% ranges contain the later reports (north 120/120, east 120/120, up 120/120). Lag-one normalized-error correlations range from 0.928 to 0.999; these 120 reports are not independent coverage trials.

This is a second start time in the **same opened flight**. It checks temporal transfer but does not calibrate prediction-error coverage on independent aircraft or select an Earth model. The [machine-readable result](ROLLING_ORIGIN_200_CONDITIONAL_RESULT.json) retains signed errors, numerical dispositions and hashes. Seven reserved ESA flight groups remain closed.
