# Joint future-path conditioning checked

The [fixed software plan](CONDITIONAL_JOINT_PROFILE_PLAN.md) now applies
one Gaussian error operator to the entire training-plus-future residual
and to **every** calibration Jacobian column. It retains the future
innovations for the bounded whole-path compatibility profile. Nine focused
checks pass across this adapter and the profile helper.

An independently assembled small dense covariance gives the same
conditional future quadratic value for multiple nuisance corrections.
Its separately solved bounded profile also agrees. A calibration column
affecting only earlier observations still changes the conditioned future,
as it should; the software does not silently discard that dependence.

This verifies linear conditional algebra only. The operator assumes a
specified Gaussian law. Later observations choose the profiled correction,
so the result is **not** a held-out prediction score. There is no
Earth-model comparison, empirical aircraft error calibration, nonlinear
remainder bound, null distribution or scientific decision. No original or
reserved flight was read. The next gate is a finite generated case with
known truth and an independent nonlinear path comparison before applying
the score to opened aircraft development data.
