# A tighter static force bound

All 24 controls pass. The new static height range is about 9–31% as wide as the
old norm-based range on the tested nonfixed domains. All 1,158 independent
point checks remain inside the supplied bounds, using the declared numerical
comparison margin. Work accounting reconciles all 6,948 scalar checks.

The improvement comes from preserving direction. Yaw and sideways tilt cannot
be treated interchangeably when bounding the vertical component of force.
The construction retains signed increments, accelerometer calibration ranges
and the supplied installation matrix; it does not estimate their true values.

For a coordinate unit vector `u`, write force as `f = a u + h`, with `h`
perpendicular to `u`. The bound on `u · R u` comes from the rotation derivation.
The cross term satisfies `|u · R h| ≤ |h| sqrt(min(1,q))`, where
`q = |w × u|²`. This follows from orthogonality and
`|Rᵀu − u|² ≤ q`. Interval multiplication covers the uncertain signed value of
`a`. The installation map is applied afterward with exact interval arithmetic.
The square-root endpoint is checked by exact squaring.

This is a static component result. The native controls subsequently passed,
but the [complete prediction attempt](../ilvis0-directional-prediction/INTERPRETATION.md)
did not improve the completed globe groups. Its existing training-derived
acceleration range was already tighter than this physical-only bound. The
53-stretch findings are unchanged.

[Complete controls](README.md) · [Frozen scope](PLAN.md) ·
[Rotation derivation](../ilvis0-directional-rotation/README.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
