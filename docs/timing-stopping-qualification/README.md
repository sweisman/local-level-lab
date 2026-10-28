# Analytical qualification of timing-aware stopping

32/32 fits meet their declared known answers; 8/8 direct controls behave as specified.
These are analytical software controls, not aircraft measurements.

| Known-answer objective | Returned starts | Predicted observations agree |
|---|---:|---|
| interior | 4/4 | True |
| boundary | 4/4 | True |
| nonlinear | 4/4 | True |
| curved_redundant | 4/4 | True |
| kink_zero | 4/4 | True |
| kink_shifted | 4/4 | True |
| timed_quadratic | 4/4 | True |
| timed_redundant27 | 4/4 | True |

A rejected non-minimum is a successful rejection control, not a converged fit.
All failures remain in the evidence. Numerical software qualification establishes no statistical confidence.
A separate native optimizer qualification is required before another calibration release.

[Every result](results.csv) · [Start comparisons](pairs.csv) · [Frozen plan](PLAN.md) · [Next analyses](../NEXT_STEPS.md).
