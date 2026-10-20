# Shared-reference native qualification

Freeze 24 generated identities, using byte-identical inputs from the completed
regrouped-native qualification: all three candidates, both processing cases and
the same tangent, packet-boundary, broad-region and independent stationary-pose
controls. Physical models and all 27 calibration limits remain unchanged.

The new candidate separates six bounded reference-error coordinates from the
unshared remainder. Every probe must subtract its actual known-control shared
vectors before checking that remainder. The common block must cover those
vectors, preserve all 33 enclosure columns and carry its source/expansion
binding. Missing blocks or changed input identities must fail explicitly.

Acceptance retains the existing limits: centers/known poses within 1 micrometre,
all 162 finite-difference physical tangent-column checks within 20 micrometres
per normalized parameter at the fixed 0.002 step, and probe residuals within
the factored remainder plus the declared 10 micrometre arithmetic allowance.
Normalized known-control shared vectors must stay inside their declared boxes,
with 1e-12 comparison tolerance. None of these numerical checks establishes a
whole-program floating-point enclosure. A failure stops the sequence; it cannot
be repaired by dropping a physical direction or assigning errors independently
at every epoch.

Limits: **78 native evaluations / 19,632 native packet visits**, **348 bound
evaluations / 7,536 reserved bound packet steps**, and a new **180-second
cooperative ceiling**. Tangent identities reserve one native call and 55 bounds;
other identities reserve four native calls and one bound. Charge before every
operation. One worker reserves four numerical threads. Preserve all native
values/Jacobians, common vectors, full bounds, coefficients and failures. No
observed fits, original-file reads, protected ESA evaluation, retries,
extensions, signals or reuse of a completed allowance.

Local component tests also check the exact radial constant-velocity/time product,
static lever at a nonzero expansion center and source-binding rejection. This
finite native study precedes a separate joint 33-coordinate support interface
qualification and a separately frozen usefulness comparison. It does not by
itself establish long-record usefulness, receiver-error adequacy or observational
coverage. All scientific outputs abstain.

[Native factorization](../ilvis0-shared-reference-native/NATIVE_DECOMPOSITION.md) ·
[Earlier native controls](../ilvis0-regrouped-controls/INTERPRETATION.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
