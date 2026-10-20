# A common training-only receiver-error assessment

The native contraction experiment preserves correctness but remains too broad
for useful predictions. In parallel with that limitation, qualify a common error
assessment using receiver observations alone. It must not let a poorly fitting
Earth candidate inflate its own noise allowance.

## Mathematical component

Use a fixed time-polynomial reference with degrees 3, 5 and 7. Any numerical
reference coefficients may be used: their exact residual norm is at least the
minimum over that fixed reference space. Use the conservative noise dimension
`n - p`, counting every reference column, rather than an estimated SVD rank.
No Earth-model residual, gyro value or future receiver position enters the source.

Qualify an exact-rational alternative to the existing
`lll.ilvis0_reference_scale.fixed_reference_scale`. Define the discrete covariance
law explicitly with one OU component, a constant offset, a linear drift and
positive white noise. Record its rationalized fixed transition coefficients and
all variances. Evaluate the residual quadratic form with scalar state-space
innovations in rational arithmetic; do not build a whole-record dense covariance.

For a central chi-square with `d` degrees, inverse moments give

\[
\Pr[\chi_d^2\leq q]\leq
q^k\Big/\prod_{j=1}^k(d-2j),\qquad d>2k.
\]

Choose a lower quantile floor using integer/rational comparisons, independently
of observations. Noncentral lower-tail dominance and `rank <= p` then permit a
conservative scale upper bound from any reference residual. Return an outward
square-root endpoint checked against the exact rational quadratic form. An
unsupported domain, precision limit or time allowance must abstain.

Test exact quadratic forms against independent small dense references, rank
loss, poor reference means, quantile certificates, extreme numerical scales and
cooperative precision/runtime limits. Benchmark generated prefixes before
choosing an observed-source allowance. Preserve all earlier source freezes.

## Recorded-data development assessment

Only after software qualification, freeze the first 292 receiver epochs of the
already studied recording `570b37d23af5e245dd461051`. Its later GPS positions are
absent from the assessment API. Use an observation-independent coordinate chart
with fixed latitude/longitude scales and height in metres; identify that chart
separately from the older receiver-position-dependent error metric.

Predeclare two discrete correlation families corresponding approximately to
10-second and 300-second OU times. Their reference standard deviations are
0.3/0.3/0.7 chart metres for white error, and 1/1/3 for each correlated, offset
and drift component. Anchor drift to training timestamps. Report all six
covariance/reference combinations; do not choose one using model rankings.

Inputs, sources, chart, reference designs, covariance coefficients and finite
work limits must freeze before calculation. Read saved receiver data only;
zero original-IMU reads, native predictions, Earth-model fits or protected ESA
evaluations. The assessment remains retrospective development.

## Limits of the result

The method supplies a conservative scale **under a declared Gaussian covariance
law**. It cannot establish that the law describes actual receiver errors or
turn a reference residual into measured receiver accuracy. Mean misspecification
can widen the bound. No automatic transfer to old covariance policies, other
recordings, ESA, or production decisions is allowed.

This does not repair the wide nonlinear prediction ranges. Joint calibration
structure, global numerical treatment, absolute withheld adequacy and independent
confirmation remain separate requirements. No observed prediction fit follows
from this component alone.

[Saved prediction evidence](../ilvis0-saved-prediction-comparison/INTERPRETATION.md) ·
[Native limitation](../ilvis0-native-training-contraction/INTERPRETATION.md) ·
[Earlier shared-scale mathematics](../ilvis0-shared-reference-scale/MATHEMATICS.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
