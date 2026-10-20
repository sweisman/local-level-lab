# Recording-scale bound growth and numerical agreement

This is a generated-input feasibility study, not a new aircraft comparison.
The question is whether the full parameter-region bounds remain finite and
informative over a four-minute, 200 Hz history, and how the mathematical center
agrees with both unchanged native kernels at that scale.

## Frozen scope

Six histories: the three candidates under a broad and a separately declared
narrow calibration box. Each contains 48,000 original generated packets, with
checkpoints at 100, 1,000, 10,000 and 48,000 packets (0.5, 5, 50 and 240 seconds).
Shared calibration, initialization and processing remain unchanged across each
history. The narrower box is a sensitivity assumption, not inferred calibration.
All 27 columns remain present; timing is fixed at a supported packet endpoint.
The separate short-history study covers crossing-boundary timing.

Propagate increment/global geographic bounds sequentially. Stop a history if its
outer region crosses a coordinate/denominator domain or becomes nonfinite, and
record exactly where; do not clip it, reduce its bounds or retry. A wide region
is a feasibility result rather than a successful prediction. Preserve all
generated inputs and the executed-step count.

At each supported checkpoint, compare the mathematical center with both native
predictions and retain the complete C++ tangent. Four fixed parameter probes
(center, all lower bounds, all upper bounds and one fixed-seed point) check
change/remainder containment against the same global bounds. Allow 1 mm in
fixed-seed metre coordinates for finite arithmetic and `2e-12*norm(linear_term)`;
record discrepancies separately. This is an empirical arithmetic comparison,
not a formal whole-program roundoff certificate or calibrated aircraft coverage.

## Finite allowance

Six charged identities, 288,000 maximum bound steps, 96 maximum C full-history
calls, 24 maximum C++ tangent calls and 96 probes. No optimizer, original archive
reads or protected outcomes. One worker/four numerical threads, 900 cooperative
seconds, no signals. Reserve an identity's full allowance before execution.
Unused calls after an unsupported region remain charged and cannot be reused.

Freeze all generated inputs, sources, compiler binaries/flags and environment.
Publish verified results, including unsupported histories and limits on numerical
claims. The original 53 comparisons remain unchanged. New withheld predictions
still require shared observational-error assessment and an adequate numerical
and nonlinear-error treatment over the region actually used.

[Short-history controls](../ilvis0-history-bounds/INTERPRETATION.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
