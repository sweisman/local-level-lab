# Reconstructed correction candidates

The 80-fit forecast extension preserved each fit's local residual, Jacobian
and normalized parameters. A [saved-only reconstruction](remaining-correction-candidates.json)
solved the same bounded linear correction for all **49** fits whose fresh
probe failed. For every one, its predicted cost change, residual step and
parameter step reproduce the stored probe values. It used **zero native
evaluations**, no original recordings and no withheld receiver positions.

The median predicted cost change is `1.56e-9`. For **31/49** candidates the
linear calculation predicts a change at or below the frozen `1e-8` limit,
while the actual fresh evaluation failed that limit. The other 18 already
exceed the limit in the local calculation. This locates a mismatch between
some local corrections and their actual fresh costs; it does not identify
whether the cause is nonlinear propagation, numerical precision or another
part of the fitted observation model.

The reconstructed vectors are inputs for a separately charged development
check of **forecast-path stability**. They are not new fits or accepted
solutions. All 50 original numerical failures remain failures, and no Earth
model ranking changes.

[Original forecast result](REMAINING_GROUPS_PREDICTION_RESULT.md) ·
[Stopping audit](REMAINING_GROUPS_STOPPING_AUDIT.md) ·
[Next solver gate](NEXT_SOLVER_QUALIFICATION.md)
