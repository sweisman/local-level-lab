# Carry shared rate-point errors through native motion

The separately checked rate-point law needs twelve hidden coordinates rather
than six: changing bias and the preceding white sample on each sensor axis.
Connect it to the shared native-history implementation without copying the
motion equations or changing the incremental-data law.

Use 21 pose/noise coordinates for rate-point input. Keep the original 15-state
incremental path. Preserve the long-double nominal state, correction signs,
all sensor axes and the existing binary64 packet/query associations. A partial
native query keeps the frozen fraction of the converted full-packet increment;
do not introduce a new interpolation convention or independent partial noise.

Compress process and observation loadings jointly where required. With both
receiver components, offsets and drift, the combined rate-point path needs
33 states. Extend the bounded innovations/receiver interfaces sufficiently to
support that case, retaining explicit memory limits and zero components. Do not
drop nuisance states or change covariance to fit the old software dimension cap.

Retain independent finite-difference and nominal-reference checks for both
input laws across the twelve candidate/processing/gravity combinations. Longer
checks use at most 600 packets and nine queries; short checks use at most two
packets with interior queries and all initial/endpoint driver directions.
Retain the existing covariance and receiver software regressions and the
combined incremental-input checks. Include the full 33-state receiver path.

Freeze a fresh qualification with at most 26,000 native calls, 42,000
conservative packet steps, two cached builds, one numerical thread and a
cooperative ten-minute allowance. No random draws, optimizer starts, original
reads or protected reads occur. Completed allowances remain unchanged.

Precharge each generated case's full declared native/packet allowance durably
before execution, then enforce its remaining allowance before every call.
Interrupted cases retain the full charge and cannot restart. Record actual
completed work separately. This preserves the work bound while avoiding one
durable database transaction for every packet. Qualify the accounting helper
on rejection, overspend, interruption and duplicate-start controls first.

Passing these controls would qualify source-specific fixed-calibration error
propagation. Training-only calibration at bounds and nonlinear prediction
coverage would still need qualification before broader aircraft fits. Neither
input law estimates the actual instrument noise.

[Rate-point law](../integrated-noise-covariance/POINT_PLAN.md) ·
[Native history](README.md) · [Prediction assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
