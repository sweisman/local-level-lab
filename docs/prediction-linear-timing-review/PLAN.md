# Saved linear-correction timing review

## Question

Does the correction used by the saved numerical stability check cross an IMU
integration boundary? Compare the two failed starts with the same two settings
from the preceding, successful noise family. Boundary proximity alone is not a
diagnosis; the successful controls are needed too.

## Fixed scope

Use the closed fresh calibration only. Select seeds 281474977010692 and
281474977010693, rate-sample errors, specified-field globe, field removal
allowed, starts 0 and 1: four existing records. Preserve their failure labels.

Replay each saved bounded linear least-squares correction once, with all 27
columns, its original bounds, tolerance 10⁻¹⁰ and 100-iteration ceiling. Verify
its predicted cost change and step norm against the saved stability probe before
interpreting the timing step. Use the source-bound, hash-verified clock routine
to report which receiver queries cross boundaries.

This is saved-matrix algebra, not a new nonlinear fit or a calibration campaign.
It permits **four charged linear solves**, one thread and a ten-minute
cooperative ceiling, with no retries, native calls, regenerated measurements or
new noise draws. Interrupted solves remain charged. Known-answer software tests
must pass before reading the four study matrices.

## Next gate

Publish both controls and both failures, even if a linear replay does not match.
The result can identify a useful derivative test; it cannot qualify a failed fit
or prove a physical cause. Any native probe, revised solver or fresh campaign
still requires its separate reviewed finite plan.

[Saved clock review](prediction-clock-boundary-review/README.md) ·
[Next analyses](NEXT_STEPS.md).
