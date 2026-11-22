# Noisy versus clean generated IMU increments

The two saved noisy streams were compared with the same deterministic clean generator. No fit or native forecast was run. Signed sums are shown in **sensor body axes**; they are input diagnostics, not a navigation-frame turn or a position forecast.

| Injected error law | Sum of angle-increment difference X/Y/Z (degrees) | Sum of velocity-increment difference X/Y/Z (m/s) |
| --- | --- | --- |
| increment | -0.0043, 0.0043, 0.0147 | 0.0445, 0.0143, -0.0736 |
| point | -0.0217, -0.0155, 0.0004 | -0.0439, 0.0249, 0.0077 |

These differences include injected random error and changing bias. They do not isolate a single component or establish the observed aircraft error law. The [machine-readable report](ORACLE_NOISE_DIAGNOSTIC.json) also records half-period sums, rate-equivalent RMS values and hashes.
