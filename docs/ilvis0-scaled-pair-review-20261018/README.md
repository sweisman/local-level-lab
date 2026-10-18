# Complete comparison after scaling the affine correction

**Shape preference: globe.** All six primary fits, both scheduled repeat pairs and both fresh controls pass. Both processing cases also prefer the specified background field after shape is resolved.

The local solver previously reported success for a correction that worsened its own linearized cost. Rescaling the affine correction box fixed that numerical failure while preserving every physical parameter, bound and full native acceptance check. The matched trial passed all four checks in 54 native calls. This review added **zero native predictions, fits or original-file reads**; it compared two saved residual pairs.

| Processing case | Globe with field cost | Zero-field globe cost | Flat-disc cost | Repeat cost difference | Largest axis track RMS |
|---|---:|---:|---:|---:|---:|
| bias1_profiled_removal | 2.444154 | 1997.850407 | 9367.286617 | 4.33693e-09 | 5.71911e-06 m |
| bias1_unsubtracted | 2.444154 | 1997.850407 | 16650.685347 | 6.0872e-11 | 1.23792e-05 m |

The required repeat limits are relative cost difference 10⁻⁶ and per-axis track RMS 0.01 m. These are numerical repeatability limits, not instrument-accuracy estimates or calibrated significance. All twelve outcomes from the three focused trials remain recorded, including the two initial preflight errors and two later native stability failures. No error is assigned an invented native fit cost. The original interval, observations, clock, receiver weights and physical bounds remain unchanged.

The comparison measures support for the specified field versus zero; it does not identify the field’s cause or distinguish solar and sidereal rates. Overlapping recordings require shared-flight grouping.

[Current status](../CURRENT_STATUS.md) · [All stretches](../ilvis0-current-findings-20261015/STRETCHES.md) · [Underlying trial](../ilvis0-scaled-pair-boundary-20261018/RESULTS.md) · [Numerical diagnosis](../ilvis0-correction-audit-20261018/INTERPRETATION.md).
