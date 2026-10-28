# Qualify compensated arithmetic during fitting

**Question:** Does the corrected arithmetic pass the unchanged optimizer checks
when fitting generated measurements, rather than only evaluating saved points?

The [complete saved-point diagnostic](saved-point-coordinate-precision/INTERPRETATION.md)
passes all 315 derivative comparisons and four stopping probes. This permits
optimizer qualification, not a restart of the stopped calibration campaign.

## Fixed experiment

Use the two already exposed simulated seed families, 281474976810725 and
281474976810726. For each, retain all three generating physical candidates,
both processing assumptions, both declared input-error formats and both original
starts: **48 fits**. These are development examples selected to include the
previous failure, not independent confirmation or a calibration sample.

Preserve the two-minute trajectories, 300 Hz input, 119 receiver epochs,
earlier-only initialization, original calibration bounds, gravity treatment,
noise settings, covariance anchor and full 26/27-column problems. Change only
the mean integration arithmetic to the qualified compensated implementation.
Keep the original noise propagation. Reconstruct the four earlier saved-point
input bindings and error operators exactly; never relabel the original fits.

Each fit has at most **200 evaluations**, one continuous forecast, no retries
and no alternative starts. Use **four workers with one thread each** and a
**two-hour cooperative ceiling**. Prepay the existing per-case construction and
native caps: 2,877,792 native operations and 18,072,612,144 conservative
packet-query visits overall. Allow two compiler builds per worker: original
noise bridge and compensated tangent. No aircraft or protected inputs are read.
Unused allowance remains charged; a failed or interrupted task is preserved.

## Qualification gates

Before freezing, test the optional native-provider interface with its unchanged
default path; reject altered tasks, sources, environments and failed parent
checks before work. Exercise the real compensated full protocol in all twelve
model/processing/error-format combinations on short generated examples.
Their small evaluation cap tests integration and accounting, not convergence.

For the full experiment, report separately:

- Every original numerical stopping decision and physical prediction screen.
- Objective agreement between the two prescribed starts, using the original
  relative-cost tolerance of 1e-8.
- Agreement of the two reconstructed training tracks, using the original
  1 mm per-axis RMS and 10 mm maximum position-stability limits.
- All parameter boundaries and unavailable outcomes. Parameter agreement is
  not required where parameters are unidentifiable.

The method qualifies on this matrix only if all 48 fits pass numerical and
physical checks, all 24 start pairs pass objective/track agreement, and the four
saved input/error bindings reproduce exactly. A failure blocks calibration;
do not expand this experiment, change its gates or retry a failure.

## Shared implementation and verification

1. Add an optional kernel-provider argument to `lll.structured_noisy_study.run_case`;
   preserve its default, prepayment, construction, forecasts and failure records.
2. Add `lll.coordinate_optimizer_study` as a small definition/evaluator using that
   shared runner, the existing generated-truth implementation and shared lifecycle.
   Freeze the qualified arithmetic, environment, original points and finite matrix.
3. Add `lll.coordinate_optimizer_report` to audit saved results and start pairs.
   Reporting must never fit, generate inputs or reclassify old failures.
4. Verify focused deterministic tests, prepare the source-bound qualification,
   then launch only its frozen matrix. Audit and publish every outcome, update
   the public overview and status registry, and retain reproducible archives.

Fresh calibration, independent validation and observed fitting require their
own subsequent finite release. The 53-stretch findings remain unchanged.

[Roadmap](ANALYSIS_ROADMAP.md) · [Next analyses](NEXT_STEPS.md).
