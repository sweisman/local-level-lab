# Timing adapter software qualification

The remaining six stretches have eleven unfinished primary fits and eight
unfinished repeats. Their packet transitions occur in narrow clusters. A nearest
transition changes only one receiver epoch and need not minimize the complete
objective. The adapter therefore searches for an adjacent negative-to-positive
timing-gradient crossing before running the qualified two-sided stopping check.

This software qualification uses known functions, a compiled clock-only reference,
and three independently specified straight-motion tracks through the compiled IMU
integrator. It reads no archive originals and makes no observed-data fit starts.
It tests local numerical behavior, not observational uncertainty or Earth geometry.

## Frozen scope

- One test batch, thirty controls, no retries, ten-minute timeout.
- One numerical worker, four threads, zero reserved threads.
- At most 2,048 analytic callbacks, 78 compiled motion evaluations, 256 affine
  solves and 1,000,000 clock comparisons across these software controls.
- The executable adapter enforces 26 callbacks per diagnosis and twelve derivative
  samples per timing search. Its clock enumeration has a separate 200,000-query
  limit, with 1,024 queries reserved for adjacent-interval verification.
- Preserve the qualified two-sided policy, physical bounds and numerical limits.

Controls cover separate close transitions, native clock agreement at adjacent
representable doubles, nonmonotone gradients, missing brackets, finite budgets,
discontinuous values, nuisance instability, repeat failure, relocation checks and
closed-form motion predictions. A local sign bracket is not a global optimum.

The archive runner still needs its own finite freeze and lifecycle checks. Passing
this batch does not change any of the 47 globe / zero flat / six unresolved results.
