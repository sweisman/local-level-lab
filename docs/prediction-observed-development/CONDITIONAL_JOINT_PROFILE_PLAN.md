# Conditioned whole-path profile: software gate

The [bounded path algebra](JOINT_FUTURE_PROFILE_RESULT.md) currently accepts
vectors already whitened under a supplied error law. This control binds it to
the existing fixed-design `LinearInnovations` operator without using any
aircraft observation. The operator and training split must be fixed before
later values are supplied.

Whiten the **complete** residual and every calibration Jacobian column with
one operator, then retain only the future innovations. This preserves the
effect of each calibration change on the earlier residual and therefore on
the conditional future mean. Profile one bounded correction over those
future innovations. Reject missing rows/columns, a mismatched operator,
nonfinite inputs and an empty training or future block. Do not drop weak or
unidentifiable nuisance columns.

Compare the future whitened quadratic form with an independently assembled
small dense Gaussian covariance and its Schur-complement conditional form
for multiple fixed nuisance corrections. Test that a training-only change in
a nuisance column affects the conditioned future as expected. This is a
mathematical/software qualification, not a fit of an Earth hypothesis.

Later observations still choose the profiled correction. Thus it remains a
conditional compatibility score rather than a held-out prediction error.
No null law, aircraft error law, nonlinear validity, model winner or
scientific decision is authorized. Synthetic matrices only, one thread,
zero native integrations, fits, original files or protected groups.
