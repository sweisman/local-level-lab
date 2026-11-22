# Check the saved variance and persistence solutions

All sixteen starts in the [joint error study](ESA_JOINT_PERSISTENCE_RESULT.md)
hit the evaluation cap. Keep those statuses. Check the eight selected donor
settings before deciding whether more optimization would change anything.

Use the exact saved six donor windows per fold. Independently differentiate
the same Gaussian likelihood with respect to all six log parameters. Keep the
native factors, additional covariance roots and forecast paths unchanged.
Check the gradient and likelihood against the dense calculation on generated
examples. On the saved points, reproduce the donor log scores and compare
the analytic derivatives with step-size-controlled finite differences.

Report the gradient in all six log coordinates and the allowable descent at
active bounds. Report the step sizes and derivative discrepancies. This is a
saved-point diagnostic. It will not certify global optimality or turn a
budget-exhausted search into a converged fit. Read no omitted positions,
original recordings or reserved flights. No parameter is reoptimized here.

Freeze eight tasks, each with one analytic score, one replay of the prior
score and 24 finite-difference probes. Use log-coordinate step sizes of
0.0001 and 0.00005. Use centred differences where both steps fit inside the
original bounds and second-order one-sided differences elsewhere. Record
exact-bound projected derivatives. Compare the replay and analytic scores at
an absolute tolerance of 0.000001. The derivative discrepancy is measured
and reported without assigning a new optimization stopping criterion.
Each score uses six donors. Allow two one-thread workers, a 180-second
cooperative deadline and zero new numerical starts for model fitting.
