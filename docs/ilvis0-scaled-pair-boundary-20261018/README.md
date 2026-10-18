# Scaling the local calibration correction

The [saved-system audit](../ilvis0-correction-audit-20261018/INTERPRETATION.md)
found that a bounded local solver could report success while making its own
linearized fit worse. The fresh native stability check correctly rejected
that step. Both remaining starts of the nearby timing pair reproduce the issue.

The new candidate rescales each affine correction coordinate by its permitted
range, preserving all parameters and physical bounds. It also verifies that a
proposed affine solution beats a known feasible reference. The final checks
against the actual nonlinear predictions remain unchanged.

The [finite plan](PLAN.md) qualifies the candidate on known answers and the exact
saved failing systems before observed work. The matched trial includes two fresh
controls and the missing primary/repeat pair: at most 58 native evaluations,
four threads, no optimizer starts and no retries.

The trial is complete: **all four checks passed in 54 native evaluations**.
The [complete saved review](../ilvis0-scaled-pair-review-20261018/README.md)
also passed all model/case/repeat requirements, bringing the published tally to
**52 globe / 0 flat / 1 unresolved**. Earlier failed trials remain preserved;
the completed allowance cannot be reused.
