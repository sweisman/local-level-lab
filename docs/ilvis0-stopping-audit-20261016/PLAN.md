# Stopping-gate and unresolved-endpoint audit

The current tally is 47 globe preferences, zero flat and six unresolved stretches.
One unresolved stretch has direct native evidence of a timing-derivative change at
a packet boundary. This saved-only audit examines whether that pattern extends to
the other five and whether the original stopping gate is necessary for optimality
at a nonsmooth minimum.

Fixed scope, with no original-recording reads, native predictions or observed fits:

- All six unresolved stretches in the verified current publication, selected by
  disposition alone. Inspect the eleven unfinished primary identities and their
  eleven scheduled repeats: **22 endpoints**. Preserve passing repeats too.
- Reconstruct the frozen nominal packet clock by accumulating 0.005-second
  intervals, using each task's preserved packet count. Combine this with saved
  receiver epochs and fitted time offsets. Report nearest-boundary distances and
  epoch fractions within 100 ns, 1 µs and 10 µs, plus branch changes under ±100 ns.
  These are descriptive screens, not new scientific eligibility thresholds.
- Read each endpoint's hashed saved residual/Jacobian. Compare three affine
  corrections: the original full correction, a correction restricted to the
  current packet interval, and one holding time offset fixed. **66 affine solves
  maximum**. An affine improvement is not a verified full-model improvement.
- Preserve saved stationarity and physical-stability outcomes. Recover the sign
  of the old fresh-probe objective change only when the saved central objective
  reproduces; otherwise fail the audit rather than infer its sign.
- Five independent known-answer gate controls: left/right derivatives of a true
  cusp minimum, a smooth minimum, a constrained-bound minimum and a smooth
  nonminimum. **Ten analytic evaluations / five gate solves**. The cusp objective
  is `(1 + 0.001 abs(u))² + 1600` on `[-1,1]`; its minimum is known without fitting.
  The physical conversion is an explicitly arbitrary software-control mapping,
  not an assumed IMU specification or a change to the observation covariance.

Freeze sources, selected identities, artifact hashes, environment and finite
counts before the once-charged audit. Use at most four numerical threads.
Interrupted batches remain charged; completed work renders saved results only.
Retain original convergence/disposition labels. No new observed fitting allowance,
stopping rule or rollout is authorized by these local diagnostics.
