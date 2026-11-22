# Error scales on the matched long generated trajectory

The two sealed calculations use the same clean aircraft trajectory, known initial state and known calibration as the saved noisy forecasts. Only future reports 600–899 are compared; no future receiver errors enter the forecast-error scale.

| Generated error law | Expected horizontal RMS scale (m) | Observed horizontal RMS (m) | Ratio | Expected vertical RMS scale (m) | Observed vertical RMS (m) | Ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| increment | 350.7 | 59.7 | 0.17 | 14.6 | 31.9 | 2.19 |
| point | 350.7 | 637.1 | 1.82 | 14.6 | 7.1 | 0.49 |

These are two fixed generated draws. The expected scales assume the declared synthetic error laws and exact nominal geometry. The ratios do not establish coverage or identify the error process in an ESA recording. The seven reserved confirmation groups remain closed. [Machine-readable values](ORACLE_MATCHED_SCALE_REPORT.json) retain source and study hashes.
