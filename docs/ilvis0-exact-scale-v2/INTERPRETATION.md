# The exact error calculation passes

All **16 software controls pass**, including both 292-epoch prefixes. Eight
small cases match independent exact matrix calculations. Each longest prefix
takes about 5.1 seconds. No aircraft observations or model fits were used.

The [first version](../ilvis0-exact-scale-qualification/README.md) stopped while
printing a large rational number. Its failure remains preserved. This version
changes only the bounded output capacity; the mathematics, generated inputs
and acceptance tests are unchanged.

## What the bound means

Write the training observations as `y = mean + scale × Gaussian error`, with a
fixed positive-definite covariance shape `C`. Choose a fixed reference space
`X` with `p` columns. Any fitted coefficients are allowed: their residual
quadratic form `Q` is at least the minimum over that reference space.

If its actual rank is `r <= p`, the minimum divided by the true squared scale
has a noncentral chi-square law with `n-r` degrees. Noncentrality moves mass
away from zero; reducing the degrees to `d = n-p` is conservative for the lower
tail. Thus a certified lower-tail floor `q` gives the scale upper bound
`sqrt(Q/q)`. Poor reference means can make this bound larger; they cannot
invalidate it by requiring an Earth candidate to supply its own noise level.

For an integer `k < d/2`, the inverse chi-square moment is
`1 / product(d-2j, j=1..k)`. Markov's inequality therefore bounds the probability
below `q` by `q^k / product(d-2j)`. The calculation selects a dyadic `q` using
integer comparisons and checks the final floating-point square-root endpoint
by exact rational squaring. No numerical rank cutoff or floating-point
chi-square quantile determines that guarantee.

The covariance combines a discrete OU state, constant offset, linear drift and
positive white noise. Exact state-space innovations avoid a dense whole-record
matrix. The OU transition is explicitly rationalized, rather than presented as
an exact continuous-time exponential.

## Next gate

Prepare a separate assessment using only the first 292 receiver epochs of the
already studied recording. Report every predeclared reference/covariance case.
Its scale bounds remain valid only under their declared Gaussian error law;
they do not establish actual receiver accuracy or calibrated aircraft coverage.

This result also leaves the broad nonlinear prediction ranges unresolved.
No observed Earth-model fits or protected ESA outcomes follow from this pass.

[Results and frozen limits](README.md) ·
[Training-only source plan](../ilvis0-shared-training-error/PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
