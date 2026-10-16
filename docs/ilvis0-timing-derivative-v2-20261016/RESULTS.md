# Native timing-derivative checks

Finished 2 scheduled endpoints: 2 successful / 0 errors; 24 native calls, with zero optimizer starts. The completed control is reused unchanged from the preceding diagnostic; no control is rerun. These fixed-endpoint diagnostics preserve every scientific disposition and stopping limit.

[Preserved control and earlier preflight errors](../ilvis0-timing-derivative-20261016/RESULTS.md).

| Endpoint | Time step (ms) | Centered derivative relative error | Left/right difference | Packet changes − / + |
|---|---:|---:|---:|---:|
| primary | 0.0001 | 0.00047573 | 0.000955132 | 0 / 354 |
| primary | 0.01 | 0.000620473 | 0.00124098 | 0 / 354 |
| primary | 1 | 0.000622894 | 0.00124509 | 0 / 354 |
| primary | 4 | 0.000625996 | 0.00124897 | 0 / 354 |
| repeat | 0.0001 | 0.000176257 | 0.000354961 | 354 / 0 |
| repeat | 0.01 | 0.000617451 | 0.00123491 | 354 / 0 |
| repeat | 1 | 0.000620905 | 0.00124501 | 354 / 0 |
| repeat | 4 | 0.000618177 | 0.00124894 | 354 / 0 |

## Recorded coupled-endpoint rounding

| Endpoint | Parameter | Computed value | Evaluated value |
|---|---|---:|---:|
| primary | gyro_bias_x | -1.0000000000000002 | -1 |
| repeat | gyro_bias_x | -1.0000000000000002 | -1 |

The smallest steps can encounter floating-point subtraction limits. Large-step differences may reflect real changes between adjacent measured increments; neither is automatically a derivative defect. The saved [measurements](summary.json) include per-axis errors, signed objective changes, packet distances and full/half coupled corrections. No result is relabeled.
