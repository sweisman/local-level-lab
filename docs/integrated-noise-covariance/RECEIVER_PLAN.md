# Carry receiver errors across the prediction boundary

The native-history gate propagates inertial errors with an explicit independent
receiver error at each observation. The next component adds receiver offsets,
drift and up to two exponentially correlated error components. It uses the
existing declared receiver law, including its fixed drift origin and span.
It does not estimate errors from a preferred fit.

Keep the existing native process/observation dependence intact. Augment the
state with independent receiver-error coordinates. A receiver observation and
its receiver-state endpoint share the same innovation. Each epoch may have
an explicit invertible coordinate/loading transformation, retaining the full
cross-axis covariance. Verify that the supplied white observation covariance
matches the declared receiver law; do not silently replace or double it.

Compress the combined process and observation loading together. Separate
compression would lose their shared drivers. Preserve singular and zero
components without variance floors, jitter or eigenvalue clipping. Keep all
native state coordinates and do not retain a dense covariance over epochs.

Compare the resulting operator with an independently formed dense covariance
on small generated examples. Check whitening of all 27 calibration columns,
earlier-only conditional predictions, changing epoch spacings, both correlated
components, offsets, drift, cross-axis transformations and zero components.
Include mismatched white-error and invalid-input rejection and a generated
maximum-state example. Neither native equations nor protected data are used.

Use one numerical thread, at most sixteen generated checks, at most sixteen
epochs per check and a cooperative two-minute allowance. No random draws,
native calls, optimizer starts, original reads or protected reads are allowed.
Freeze a fresh source/environment request before formal qualification. Do not
edit the active native-history source freeze or restart a completed study.

This qualifies fixed-parameter covariance composition. Uncertainty from fitting
calibration and noise parameters, nonlinear predictive coverage and the actual
archive error law remain separate gates. No observed fitting or confirmation
release follows from these checks alone.

[Covariance component](README.md) ·
[Native-history plan](../native-noise-linearization/HISTORY_PLAN.md) ·
[Receiver assumptions](../ESA_ERROR_POLICY.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
