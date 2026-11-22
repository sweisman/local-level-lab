# Fixed-endpoint timing check

All eight preselected recorded-data endpoints completed their ten
charged training calculations. Repeating each exact parameter vector
gave identical receiver predictions on all three axes at all eight
endpoints; every saved training cost also reproduced exactly. This
establishes deterministic replay at these points, not convergence of
their original fits.

| Time-offset step | Endpoints crossing a packet interval | Largest relative timing-derivative difference |
|---|---:|---:|
| 0.1 µs | 1/8 | 2.2e-05 |
| 10 µs | 4/8 | 3.6e-05 |
| 1 ms | 6/8 | 0.000102 |
| 4 ms | 8/8 | 0.000104 |

Packet-interval crossings occur, including at the smallest tested
step for one endpoint. Across these fixed probes, the centered
finite-difference timing response remains close to the analytic
derivative (largest relative difference about 0.000104). This does
not establish that an optimizer can cross every timing boundary
reliably or that timing explains a later forecast difference.

| Differing inner cut | Later-path spread | Time-offset difference | Largest normalized parameter differences |
|---|---:|---:|---|
| 2010 northern | 0.752 m | 0.004 ms | gravity_delta 1.106, gyro_bias_z 0.543 |
| 2015 southern | 0.320 m | 11.237 ms | lever_x 0.111, time_offset 0.075 |

The 2010 maximum pair has almost the same time offset, while the
2015 pair differs much more. Several calibration parameters also
vary. The next method check should examine the joint calibration
valley and later-path sensitivity; changing only the clock cannot be
assumed to resolve both discrepancies.

No fit was restarted, no later receiver position entered the
calculation, and no failed stopping label changed. The result is a
numerical diagnostic, not a globe/flat or background-field decision.

[Frozen plan](OBSERVED_FIXED_ENDPOINT_PLAN.md) · [All 32 signed-step results](observed-fixed-timing-steps.csv) · [Earlier fit diagnosis](OBSERVED_METHOD_V2_DIAGNOSIS.md)
