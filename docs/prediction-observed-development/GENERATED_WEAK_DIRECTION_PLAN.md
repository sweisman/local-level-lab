# Saved generated calibration-direction audit

Question: do the two physically inaccurate generated complete fits share a
weak training calibration direction?

Use only the closed two-law bound-aware pilot's saved, whitened
1800-by-26 training residual Jacobians. Verify the closed study, exact recipe,
parameter names, artifact hashes, residual convention and consistency with
the saved objective. Compute full SVD with one numerical thread. Report
singular ratios, rank at the already declared 1e-10 threshold, the weakest
direction's largest normalized-parameter loadings, its reciprocal singular
scale and sign-independent similarity across the two laws. Preserve the
original physical scores and active-bound labels.

This is a local tangent diagnosis, not a new fit, likelihood interval,
calibration measurement or proof that the weak direction caused the observed
path miss. No original or protected aircraft input is read and no Earth-model
decision is made.
