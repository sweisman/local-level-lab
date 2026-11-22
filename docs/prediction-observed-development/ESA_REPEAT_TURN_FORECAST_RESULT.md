# How four turns tested the ESA position forecasts

16 of 16 training starts converged. 8 of 8 window and error-description pairs have a scored primary forecast.
All four windows come from ESA development recording 187. The two error descriptions
for each window use the same inertial measurement unit (IMU) readings.

The errors below compare the forecast with 120 later GPS positions. Each row
uses one path for all four covariance scores. A negative score change means the
added error allowance improved the joint Gaussian score, including the penalty
for wider uncertainty. Position errors are in metres. The signed course change
describes the turn block selected from the receiver trajectory.

| First receiver index | Course change | IMU error description | Primary | North | East | Height | Horizontal | 3D | Native score | Steady change | Turn change | Both change |
| ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 22936 | -9.1° | Increment | 0 | 0.226 | 0.314 | 0.199 | 0.387 | 0.435 | -1240 | +10.36 | -62.28 | -54.04 |
| 22936 | -9.1° | Point rate | 0 | 0.226 | 0.314 | 0.199 | 0.387 | 0.435 | -1240 | +10.36 | -62.28 | -54.04 |
| 33796 | -6.6° | Increment | 0 | 1.372 | 1.149 | 0.834 | 1.789 | 1.974 | 445.8 | -964.4 | -470.5 | -1449 |
| 33796 | -6.6° | Point rate | 0 | 1.372 | 1.149 | 0.834 | 1.789 | 1.974 | 445.8 | -964.4 | -470.5 | -1449 |
| 37516 | -7.2° | Increment | 1 | 0.069 | 0.339 | 0.416 | 0.346 | 0.541 | -657.9 | -309.9 | -193.2 | -499.7 |
| 37516 | -7.2° | Point rate | 1 | 0.069 | 0.339 | 0.416 | 0.346 | 0.541 | -657.9 | -309.9 | -193.2 | -499.7 |
| 41116 | +12.7° | Increment | 0 | 0.616 | 0.838 | 0.695 | 1.040 | 1.251 | 948.3 | -749.9 | -1001 | -1711 |
| 41116 | +12.7° | Point rate | 1 | 0.616 | 0.838 | 0.695 | 1.040 | 1.251 | 948.3 | -749.9 | -1001 | -1711 |

These results measure prediction and error scoring on one development flight.
Independent flight coverage, absolute accuracy and a matched Earth-model comparison
require separate studies.

- [Forecast release receipt](esa-repeat-turn-forecast-evidence/receiver-release.json), SHA-256 `6607441aa0ae1cf43ae263a39eb4240e552d447ffe7b4a5774995cd8fe96fd3e`
- [Position and covariance scores](esa-repeat-turn-forecast-evidence/receiver-scores.json), SHA-256 `ae1fa59746e4f57cb539595afbde23d71899a7fdde73af438976c82daf3d988e`
- [Method and reproduction](ESA_REPEAT_TURN_RELEASE_RESULT.md)
