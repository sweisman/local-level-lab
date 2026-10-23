# Reconstruct saved widths with the original rounding convention

Repeat the complete six-case arithmetic audit under a new freeze. Preserve the
first audit and its four rejected cases. Its checker used ordinary subtraction
for reported widths, while the parent reports the exact endpoint difference
rounded upward. A deterministic regression now reproduces that distinction.

The correction uses the parent's outward-rounding convention and reports the
width-reporting increment separately. It does not change any prediction,
observation, model, source bound, calibration interval or earlier result.

Verify the same six parent completion/result/training/future/bound hash chains.
Reconstruct each axis width in metres from affine support, position and lever
reconstruction allowances, arithmetic and outward rounding. Keep exact fractions
and distinguish each term's share of the total width from its share of the
unshared allowance. This checks arithmetic, not the validity of supplied bounds.

Limits: six new identities, 18 arithmetic axis checks, one worker, one numerical
thread, 120 cooperative seconds, no retries or allowance expansion. Charge the
checks before execution through the shared indexed journals. No trajectory,
native, interval-map or LP calculations, new support solves, aircraft reads or
optimizer starts are authorized by this audit. Earlier usefulness failures and
all scientific labels remain unchanged.

[First audit](../ilvis0-prediction-width-budget/README.md) ·
[Static coupling](../ilvis0-static-training-coupling/README.md) ·
[Prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md) ·
[Reproducibility](../REPRODUCIBILITY.md).
