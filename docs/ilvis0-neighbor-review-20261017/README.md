# Completed adjacent-boundary comparison

**Shape result: globe.** All six primary fits passed: True. Both controls passed: True. Required repeat agreement passed: True.

The completed trial used 44 native calls; this review performed no additional fits or predictions. The same two-sided check now explicitly covers the reached neighboring timing boundary. Earlier stopping failures, measurements, physical bounds, clock and receiver weights are preserved.

| Repeat check | Measured difference | Required limit |
|---|---:|---:|
| Relative cost | 1.14797e-10 | 10⁻⁶ |
| North track RMS | 1.11629e-07 m | 0.01 m |
| East track RMS | 9.23556e-08 m | 0.01 m |
| Up track RMS | 2.1704e-08 m | 0.01 m |

| Processing case | Globe with field cost | Zero-field globe cost | Flat-disc cost |
|---|---:|---:|---:|
| bias1_profiled_removal | 0.610573 | 80.769481 | 2036.924875 |
| bias1_unsubtracted | 0.610573 | 80.741848 | 25732.139901 |

These are numerical model preferences and repeatability checks, not calibrated significance or instrument-accuracy estimates. Background-field preference follows the shape comparison; the field’s cause and solar-versus-sidereal rate are not determined.

[Current status](../CURRENT_STATUS.md) · [Full stretch table](../ilvis0-current-findings-20261015/STRETCHES.md) · [Underlying trial](../ilvis0-boundary-followup-20261016/RESULTS.md).
