# Structured covariance prerequisite

Implement the existing shared receiver-error family as an innovations filter:
white three-axis error, up to two exponentially correlated components, one
constant offset and one full-record-normalized drift component. Preserve all
cross-axis covariance, actual timestamps and declared coordinate transforms.

The implementation must match the existing dense reference for whitening,
log determinant, inverse whitening and coordinate-subset marginalization.
Residuals and every Jacobian column use the same operator. Do not construct
whole-record covariance, Cholesky or projection matrices.

Keep block continuation explicit: covariance configuration, ordering, direction
and column count must match; missing state cannot silently reset a later block.
Use positive-definite innovation solves without jitter, eigenvalue clipping or
dropped nuisance columns. Treat covariance as supplied, not observationally
estimated or calibrated. No instrument bounds or Earth-model results change.

Qualify on small independent dense comparisons, including irregular timing,
cross-axis terms, singular latent components, different coordinate units and
retained-axis permutations. A later separately frozen finite benchmark will
measure memory/runtime at long-record scale; passing small tests is not that
benchmark or qualification of native streaming integration.

This prerequisite supports training-only covariance development and ESA-scale
prediction. Bounded calibration/covariance-estimation uncertainty and predictive
adequacy remain separate requirements. No archive fits or protected ESA outcomes
are evaluated by these software controls.
