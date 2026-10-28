# Native regressions of timing-aware stopping

Completed 6/6 original-start fits; 6 pass numerical and physical checks.
These generated-data regressions add no aircraft observation or statistical confidence claim.

| Case | Earlier fit passed | New fit passed | Evaluations | Later horizontal RMS | Later height RMS |
|---|---|---|---:|---:|---:|
| 1 | True | True | 25 | 4.494 m | 0.752 m |
| 2 | True | True | 25 | 4.494 m | 0.752 m |
| 3 | False | True | 61 | 2.576 m | 0.307 m |
| 4 | False | True | 59 | 2.576 m | 0.307 m |
| 5 | False | True | 25 | 0.702 m | 1.597 m |
| 6 | False | True | 25 | 0.702 m | 1.597 m |

Earlier results retain their original labels. Every input, weight and charged operation is preserved.
Broader optimizer qualification remains a separate gate; calibration does not restart automatically.

[All fits](results.csv) · [Failed checks](verification-failures.csv) · [Start comparisons](pairs.csv) ·
[Frozen plan](PLAN.md) · [Next analyses](../NEXT_STEPS.md).
