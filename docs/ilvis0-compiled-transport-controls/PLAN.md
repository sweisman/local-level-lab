# Native qualification of compiled conservative bounds

The previous implementation passes all 24 native controls, but two longer
zero-field bounds exceeded their time limits. Runtime profiles identified
repeated exact-arithmetic radius calculations as a major cost. This study checks
a separate compiled implementation before another long-history comparison.

The reference calculations, physical domains, training constraints and all 27
physical plus 24 shared-error columns remain unchanged. Vector and matrix radius
arithmetic rounds outward, including error in the supplied reference-center
operation. The library guards binary64, nearest rounding and subnormal handling.
Compilation disables fast-math and implicit contraction. Exact-rational local
checks cover signed cancellation, underflow, large magnitudes and norm bounds.
These primitive checks do not certify every operation in the complete solver.

## Fixed matrix and acceptance checks

Reuse the original 24 generated native inputs: three candidates, two processing
assumptions and four control classes. No aircraft observations or reserved ESA
records enter this qualification. Preserve the original limits: 1 micrometre for
reference/stationary predictions, a 0.002 normalized derivative step with
20 micrometres tolerance, and 10 micrometres numerical allowance for nonlinear
containment. Every registered control must pass before the next long screen.

## Finite allowance

- 24 identities, no retries or optimizer starts.
- At most 78 native evaluations and 19,632 native packet visits.
- At most 348 bounds and 15,072 two-pass bound steps.
- Four workers, one numerical thread each; four total threads.
- 60 seconds per bound and 600 seconds for the study, checked cooperatively.
- Charge before execution; retain interrupted attempts and all failures.

The freeze records sources, generated inputs, environment and compiler. Workers
compile the bound library from their frozen source directory and record the
source and binary hashes. Earlier completed studies remain immutable. Passing
this matrix permits a separately frozen long-history performance screen; it
does not authorize observed fits or establish calibrated predictive coverage.

Launch and publication use `analysis/tests/ilvis0_compiled_native_worker.py` and
the standard guarded shard runner. Package mode performs no calculation.
