# Saved linear-system diagnosis of the right-side corrections

Use only the two completed target endpoints from the corrected-context trial.
Preserve its failed full gates, original source arrays and all earlier studies.
No result from this audit can change a stretch disposition.

The question is whether the near-zero permitted timing interval destabilizes
the bounded local correction, or whether the center tangent does not reproduce
the failing side tangent. Compare three affine solves per saved center: timing
restricted to the left interval, restricted to the right interval, and fixed at
zero correction with every other physical bound retained. The fixed-time solve
is diagnostic only; it is not a proposed replacement for a full free-time gate.

Compare their predicted costs and parameter steps with the saved native branch
corrections. Compute singular spectra for the full center Jacobian and its
non-timing columns. Keep small singular directions in the report; rank here is a
numerical diagnostic, not a new scientific acceptance threshold.

Limits: one batch, two saved endpoints, **six bounded affine solves**, at most
100 iterations per solve, **four singular decompositions**, four total numerical
threads, zero native evaluations, original-file reads or optimizer starts.
The six affine solves do not fit the archival observation model. Freeze source,
input and numerical-environment hashes before the batch; charge before numerical
work and prohibit rerun. Publish/render from saved outputs after completion.

Software checks cover independently known constrained affine optima, fixed-time
elimination, rank deficiency and malformed/nonfinite problems. If the center
Jacobian does not reproduce the observed side behavior, record that limit rather
than assigning a cause. A new native tangent-capture diagnostic would then need
its own bounded plan. Scientific stationarity/cost/position limits remain fixed.
