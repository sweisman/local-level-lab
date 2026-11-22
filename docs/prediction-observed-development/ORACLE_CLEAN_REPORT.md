# Long clean forecast control

The single frozen 900-second clean task completed. Known sensor corrections and the true initial state were supplied; no parameters were fitted. Only reports 600–899 were scored against later analytic truth.

| Stream | Future horizontal RMS (m) | Future vertical RMS (m) |
| --- | ---: | ---: |
| Clean | 0.035 | 0.322 |
| increment noise | 59.66 | 31.93 |
| point noise | 637.12 | 7.14 |

The long clean propagation is close to the analytic trajectory. The large drift in the two [noisy-stream controls](ORACLE_NOISY_REPORT.md) therefore appears only when random IMU errors are injected into this software setup. That does not identify which error component causes it or establish a measured ESA error law. The seven reserved ESA confirmation groups remain unopened.

The [machine-readable report](ORACLE_CLEAN_REPORT.json) contains exact scores and evidence hashes.
