# Finite noisy timing probe

Question: at the saved failed fit, is the local time-offset derivative a
reliable guide to the actual two-minute, noisy objective on either side of the
nearby packet boundary? This is a numerical-method check, not another fit or
an Earth-model test.

Use only the sealed generated case
`sphere_rotating-1-increment-z_gyro_boundary` from
`data/bounded-nonlinear-aircraft-v2-20261111`. Its manifest SHA-256 is
`94929800fdf681887ae62f66dcd699ad26892378672a0465709a45b7da5dd8d9`
and summary SHA-256 is
`1e2ba970c5ebc7e61799f8fe2823f744964fb8fdb5fd16b12ce5a623d23870f5`.
Reconstruct the generated IMU arrays from the unchanged frozen source and
seed, then require their complete-array hashes to match the sealed input
binding before any objective evaluation. Require the saved 79 receiver rows,
whitening operator, fitted normalized point and native source hashes to match.

At most nine residual/tangent evaluations may be charged in a separately
frozen diagnostic: the saved point, points immediately on both sides of the
packet boundary, two interior steps on each side, and the saved proposed full
timing step. Building the unchanged structured error operator also calls the
native packet kernel. Cap *all* low-level work at the original case's finite
per-task maximum: **239,816 native calls and 1,506,051,012 packet visits**;
these are new diagnostic charges, not unused allowance transferred from the
completed study. Use one worker and one numerical thread, with no solver
starts, forecast, later truth, observed data or protected data. Preserve the
fresh cost, local predicted cost, exact offset and packet
assignment at every point. Stop and report any input or source mismatch.

This probe can determine whether the saved local timing model is misleading
near this boundary. It cannot by itself qualify a changed optimizer or turn
the 23/24 combined gate into 24/24. Any proposed method change must first
pass independently seeded software controls with unchanged physical bounds
and stopping requirements.

**Preflight completed:** the `lll.bounded_noisy_timing_probe.preflight`
reconstruction matched all four complete-array SHA-256 hashes and the 79 saved
receiver rows for this case, using the 36,000 packet samples. All 239 frozen
source files matched. It made zero native calls. The nine-point objective
probe remains to be implemented and qualified.
