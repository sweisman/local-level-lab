# How the saved ESA development forecast changes with horizon

This is a retrospective view of the **same** sealed 600-report fit and its next 400 one-second receiver reports. The fit and full forecast were saved before scoring; no parameter is refitted here. The short prefixes were examined after the long forecast result was known, so they cannot become fresh withheld validation.

| First withheld reports | Increment horizontal RMS (m) | Increment height RMS (m) | Point-rate horizontal RMS (m) | Point-rate height RMS (m) |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 0.00 | 0.01 | 0.00 | 0.01 |
| 5 | 0.00 | 0.01 | 0.00 | 0.01 |
| 10 | 0.01 | 0.01 | 0.01 | 0.01 |
| 30 | 0.03 | 0.02 | 0.03 | 0.02 |
| 60 | 0.08 | 0.09 | 0.08 | 0.09 |
| 120 | 0.28 | 0.22 | 0.28 | 0.22 |
| 200 | 1.94 | 0.24 | 1.94 | 0.24 |
| 300 | 6.60 | 1.31 | 6.60 | 1.31 |
| 400 | 14.25 | 4.39 | 14.25 | 4.39 |

A shorter interval may reduce drift, but this table neither changes the failed 400-report prediction gate nor qualifies a new gate. A future short-block study must choose its windows and limits from receiver-only metadata and generated controls before examining their model errors. The seven reserved ESA groups remain sealed.

[Values and hashes](RECORDED_HORIZON_DIAGNOSTIC.json) · [Generated horizon scales](ORACLE_HORIZON_REPORT.md).
