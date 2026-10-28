# Native regressions of timing-aware stopping

Completed 4/4 original-start fits; 4 pass numerical and physical checks.
These generated-data regressions add no aircraft observation or statistical confidence claim.

| Case | Earlier fit passed | New fit passed | Evaluations | Later horizontal RMS | Later height RMS |
|---|---|---|---:|---:|---:|
| 1 | True | True | 26 | 1.082 m | 1.997 m |
| 2 | None | True | 26 | 1.082 m | 1.997 m |
| 3 | None | True | 10 | 0.942 m | 1.939 m |
| 4 | None | True | 10 | 0.942 m | 1.939 m |

Earlier results retain their original labels. Every input, weight and charged operation is preserved.
Broader optimizer qualification remains a separate gate; calibration does not restart automatically.

[All fits](results.csv) · [Failed checks](verification-failures.csv) · [Start comparisons](pairs.csv) ·
[Frozen plan](PLAN.md) · [Next analyses](../NEXT_STEPS.md).
