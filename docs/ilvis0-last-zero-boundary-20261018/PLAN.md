# Final zero-field two-sided timing checks

## Fixed question

The final unresolved stretch is `b4e44ddc0f130ecd45674c78`. Its completed
free-timing trial reproduces both zero-field solutions but fails their fresh
full-space correction check. The saved-only audit locates all four endpoints
within about two nanoseconds of a cluster of packet transitions. Fixed-time
corrections are micrometre-scale; original and range-scaled full-space solves
agree but propose a 53 ms alignment shift whose nonlinear cost increases.

Apply the already qualified range-scaled, representable-clock, two-sided
endpoint checker to those four completed zero-field endpoints. This is a
different diagnostic from the failed smooth free-timing fit. No original failed
fit is retried or relabeled. No nonlinear optimization starts are permitted.

## Scope and finite allowance

Only zero-field globe (`sphere_still`), both fixed-zero and profiled upstream
field-removal cases, and each case's primary and repeat endpoint. Two fresh
smooth controls from the completed specified-field study must pass first.

| Item | Maximum |
|---|---:|
| Fresh controls | 2 × 3 native evaluations |
| Target boundary checks | 4 × 26 native evaluations |
| Charged identities | **6** |
| Native evaluations | **110** |
| Nonlinear optimizer starts | **0** |
| Clock queries | **804,096** |
| Bounded affine solves | **10** |
| Allocation | **4 total numerical threads**, one worker |
| Retries | **0** |

The preceding study averaged about 20 seconds per native evaluation, including
extraction. At that throughput, the ceiling takes roughly 40 minutes; runtime
and early stopping can differ. Qualification is one 40-test batch, capped at
120 seconds: 30 existing candidate controls and ten scope/worker checks. The
existing controls include three independently generated compiled-motion cases
and six direct compiled-clock comparisons. No original recordings or observed
predictions are used in software qualification.

## Preservation and required gates

Hash the completed free-timing evidence, saved-only audit, controls, sources,
originals, native kernels, environment, software qualification and this plan
before launch. Verify exact saved residual/parameter/receiver/time layouts.
Full-context saved artifacts already contain the receiver timestamps and numeric
coordinates; no fused navigation quantities are introduced.

Preserve the selected observations, nominal 200 Hz clock, ±0.15-second time
bounds, ±1 degree/hour constant offsets, other physical bounds and covariance.
Use the checked local timing-only search followed by fresh full-nuisance
two-sided stationarity, correction and source-to-final movement checks. Keep
the original cost, 1 mm axis-RMS and 1 cm epoch-maximum stability limits.

Primary and repeat must pass all full endpoint checks and agree separately in
each processing case: relative cost difference at most 10⁻⁶ and per-axis track
RMS difference at most 0.01 metre. Passing one case cannot hide failure of the
other. No scientific stopping tolerance or physical bound changes.

Hold exclusive source/worker locks, charge before execution and preserve every
failure. Interrupted charges block continuation; completed identities cannot
restart. No unused allowance is transferred or expanded. A successful diagnostic
still needs a separate saved-evidence review of every model/case companion and
required repeat before any published disposition changes. No claim of global
optimality, calibrated significance or background-field causation follows.
