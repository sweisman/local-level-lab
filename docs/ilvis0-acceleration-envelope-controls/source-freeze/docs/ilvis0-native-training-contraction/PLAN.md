# Native training constraints: generated feasibility test

Test whether necessary constraints from generated training positions can narrow
the full declared calibration box without losing the known true parameters.
Use every one of the 27 native coordinates under all three candidates and both
processing cases. Reuse qualified bound primitives; change no frozen kernel,
physical calibration limit or archived result.

Each of six identities uses 400 generated 200-Hz packets. Bounds and Jacobians
are evaluated at six training times (0.2, 0.35, 0.6, 0.9, 1.2 and 1.5 seconds),
with a 1.8-second future query. The original broad calibration limits, including
full yaw uncertainty, remain. No artificial narrow sensitivity box replaces them.

Construct two training cases with declared per-coordinate measurement allowances
of 1 mm and 5 m. These are supplied deterministic control assumptions, not
estimated receiver precision. Training positions are generated at a fixed
nonzero parameter vector. Future truth is evaluated only after each contraction
and its new prediction center have been fixed; it is absent from the contractor.

Propagate a global mathematical remainder over each complete input box, including
timing and processing parameters. Build necessary affine inequalities, contract
conservatively, and recompute a future bound at the contracted box's midpoint.
Retain all directions and both noise cases. Report widths before/after even if
they do not improve. Require the known truth to survive and its future prediction
to remain inside the resulting mathematical envelope.

The numerical comparison allows 1 micrometre in native values and 1e-7 metres per
normalized derivative column, matching earlier short controls. A **declared**
10-micrometre arithmetic allowance in the constructed inequalities covers those
empirical comparison scales; it is not a global floating-point certificate.
Passing cannot establish observational coverage or authorize aircraft fits.

Finite allowance: six identities, 36 native calls, 54 bound evaluations with
21,600 reserved packet steps, twelve contractions at eight passes each, four
total numerical threads and 180 cooperative wall seconds. Reserve calls/steps
before evaluation. No retries, signals, completed-study restarts or allowance reuse.

No archive, fused navigation or protected ESA recording is read. Inputs, sources,
environment and limits freeze before execution. An overly wide result remains
overly wide: do not select favorable cases or alter limits to obtain contraction.

[Contractor qualification](../ilvis0-training-box-qualification/INTERPRETATION.md) ·
[Native source](../ilvis0-native-stream-interface/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
