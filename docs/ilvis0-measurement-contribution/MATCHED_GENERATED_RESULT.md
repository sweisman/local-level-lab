# Matched field and offset qualification result

The generated qualification **passed**. 128/128 passed the technical checks and 32/32 truth-matched fits passed the combined numerical and withheld accuracy gate.

| Gyro offset cap | Numerical stops | Truth-matched passes |
|---:|---:|---:|
| ±1°/h | 23/32 | 8/8 |
| ±3°/h | 24/32 | 8/8 |
| ±10°/h | 24/32 | 8/8 |
| ±20°/h | 24/32 | 8/8 |

12/32 matched settings had numerical stops for all four candidates. Other settings retain the unresolved alternative fits.

| Probe disposition for an unfinished fit | Fits |
|---|---:|
| fresh position probe not stable | 33 |

| Failed checks | Fits |
|---|---:|
| cost change | 32 |
| cost change and stationarity | 1 |

33/33 unfinished probes increased training cost. The largest position change was 0.591 mm on any axis. 28 of these fits stopped before exhausting their evaluation allowance.

A report replay checks the saved receiver forecasts and charges. This generated result starts no observed aircraft fits. It does not qualify the gyro-free motion constraints or establish real-aircraft prediction accuracy.

[Frozen plan](MATCHED_GENERATED_PLAN.md) · [All 128 fits](matched-generated-fits.csv)
