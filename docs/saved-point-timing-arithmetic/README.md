# Timing and coordinate arithmetic at four saved points

Completed 4/4 saved-point diagnostics with 208 residual-and-derivative evaluations.
No model was refitted and no previous fit label was changed.

| Example | Original fit | Timing checks: original → boundary change | Gyro-offset checks: original → both changes |
|---|---|---|---|
| 1 | Passed | 0/3 → 3/3 | 0/3 → 0/3 |
| 2 | Failed | 0/3 → 3/3 | 0/3 → 0/3 |
| 3 | Failed | 0/3 → 3/3 | 0/3 → 0/3 |
| 4 | Passed | 0/3 → 3/3 | 0/3 → 0/3 |

Agreement here concerns the timing and gyro-Z-offset derivative comparisons at three fixed steps.
Every nuisance column remains in the saved matrices. These are not new stopping decisions,
qualified optima, uncertainty thresholds or flight findings.

[Summary CSV](results.csv) · [Derivative curves](derivatives.csv) · [Frozen plan](PLAN.md) ·
[Previous small controls](../timing-precision-controls/INTERPRETATION.md) · [Next analyses](../NEXT_STEPS.md).
