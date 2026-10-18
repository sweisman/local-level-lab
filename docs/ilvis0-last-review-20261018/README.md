# Final stretch: complete model comparison

**Shape preference: globe.** All six primary fits, all four required repeat pairs and both fresh controls pass. Both processing assumptions also favor the specified background field over zero after the shape comparison.

The last numerical failure concerned an alignment almost at a cluster of integration boundaries. Fresh two-sided checks passed with every nuisance direction, physical bound and acceptance limit retained. The zero-field diagnostic used 102 native evaluations. This complete review added **zero native predictions, fits or original-recording reads**; it compared four saved residual pairs.

| Processing assumption | Globe with field cost | Zero-field globe cost | Flat-disc cost |
|---|---:|---:|---:|
| bias1_profiled_removal | 1.376259 | 1980.949624 | 6543.003428 |
| bias1_unsubtracted | 1.376259 | 1980.949624 | 12508.020489 |

| Repeat model / processing assumption | Relative cost difference | Largest axis track RMS |
|---|---:|---:|
| sphere_rotating / bias1_profiled_removal | 9.47381e-10 | 2.27553e-05 m |
| sphere_still / bias1_profiled_removal | 3.45167e-12 | 8.29525e-06 m |
| sphere_rotating / bias1_unsubtracted | 2.78021e-09 | 3.52552e-05 m |
| sphere_still / bias1_unsubtracted | 7.77153e-12 | 8.78682e-06 m |

Required repeat limits are 10⁻⁶ relative cost and 0.01 m RMS per axis. These are numerical repeatability limits, not instrument-accuracy measurements. All 28 focused outcomes are preserved, including fixed-time diagnostics and the failed smooth free-timing fits. Conditional profiles are never labeled fully converged. Both previously passing flat-disc primary artifacts were verified directly.

The completed comparison brings the selected corpus to **53 globe preferences, zero flat preferences and zero unresolved stretches**. This is numerical model preference; calibrated significance and independent predictive adequacy remain separate checks. Simultaneous recorders and shared flights are not independent replications. The background field’s cause and solar-versus-sidereal rate are not determined.

[Current findings](../ilvis0-current-findings-20261015/FINDINGS.md) · [All stretches](../ilvis0-current-findings-20261015/STRETCHES.md) · [Timing diagnosis](../ilvis0-last-correction-audit-20261018/INTERPRETATION.md) · [Finite plan](PLAN.md).
