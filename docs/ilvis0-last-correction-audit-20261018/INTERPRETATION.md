# The remaining failure is concentrated in timing

The audit reproduced all four failed full-space corrections from their saved
Jacobians. Each proposes about **+0.05287 seconds** of alignment change, coupled
mainly to the initial horizontal position. That changes the packet assignment
of all 434 receiver observations and crosses 4,774 packet boundaries in total.

The affine approximation predicts a cost decrease of about 0.02927. The completed
native trial instead measured an increase of about 0.01836. It accepted none
of its 39 proposed steps at any of the four endpoints, including much smaller
trust-region proposals. None exhausted its 80-evaluation solver allowance.
Merely providing more iterations would therefore not address the observed stop.

Range-scaled and original full-space solves agree closely in their correction
and predicted decrease. This differs from the preceding stretch's defective
affine correction: scaling alone does not fix the present case.

With time held fixed, the saved affine corrections predict position changes
below approximately **10 micrometres RMS per axis**. Their cost improvements
are at most about 10⁻⁹. This supports the earlier conditional profiles: the other
calibration parameters are already settled to high numerical precision at each
fixed alignment. It does not qualify the free-timing fit.

The endpoints lie approximately **0.20–1.83 nanoseconds** before a representable
packet transition. The next transition is only about 0.91 picoseconds farther
along. A smooth full-space linear approximation is therefore being used almost
at a cluster of changes in the integration interval assigned to receiver epochs.
The full Jacobians are also ill-conditioned, with largest-to-smallest singular
value ratios around 1.7–2.0 × 10⁸. These are descriptive numerical diagnostics,
not changes to a scientific rank threshold.

The next useful test is a separately bounded, fresh two-sided check at the nearby
clock transitions, retaining all nuisance directions, original bounds and
prediction-stability limits. Saved arrays alone cannot establish that a boundary
is a valid local optimum, or exclude an integration/derivative discrepancy.
Until those checks and the complete model review pass, the last stretch remains
unresolved. The published total is **52 globe / 0 flat / 1 unresolved**.

This audit used 12 affine solves, eight singular decompositions and 1,334 saved
clock queries. It made no native predictions, read no original recording and
started no observed-data fits. [Numerical report](README.md) · [Finite plan](PLAN.md).
