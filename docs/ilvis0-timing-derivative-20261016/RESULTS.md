# Native timing-derivative checks

Completed 3 endpoints / 10 native calls, with zero optimizer starts. These fixed-endpoint diagnostics preserve every scientific disposition and stopping limit.

| Endpoint | Time step (ms) | Centered derivative relative error | Left/right difference | Packet changes − / + |
|---|---:|---:|---:|---:|
| control | 0.0001 | 1.33488e-05 | 4.67879e-05 | 0 / 0 |
| control | 0.01 | 1.34431e-07 | 4.60552e-07 | 0 / 0 |
| control | 1 | 4.76071e-05 | 9.60321e-05 | 0 / 666 |
| control | 4 | 0.000118285 | 0.000238197 | 0 / 666 |
| fd7b81e48a4122b149c4925b::bias1_profiled_removal::sphere_still::primary | error | — | — | — |
| fd7b81e48a4122b149c4925b::bias1_profiled_removal::sphere_still::repeat | error | — | — | — |

The smallest steps can encounter floating-point subtraction limits. Large-step differences may reflect real changes between adjacent measured increments; neither is automatically a derivative defect. The saved [measurements](summary.json) include per-axis errors, signed objective changes, packet distances and full/half coupled corrections. No result is relabeled.
