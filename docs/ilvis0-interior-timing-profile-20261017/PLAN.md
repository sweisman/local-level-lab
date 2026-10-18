# Interior timing profile

## Question and fixed scope

For stretch `50f24131843071ae9312c082`, the zero-field-globe comparison without
profiled upstream removal has two saved time offsets about 45 ms apart. Both
starting solutions agree after nuisance refitting at either fixed time, but
the costs at the two times differ beyond the full repeat-agreement threshold.

Evaluate three interior offsets at fractions 1/4, 1/2 and 3/4 between the two
exact saved normalized offsets. At each, fit every other active nuisance
parameter from each verified endpoint's nuisance values. This makes six
predeclared fits; endpoint fits and two passing smooth controls are reused from
sealed evidence. There is no adaptive point selection or additional retry.

## Finite allowance

- Six charged fit identities; at most 80 native fitting calls each, including
  the solver's unchanged fresh stopping checks.
- One additional full native tangent per identity to preserve the final cost,
  residuals, complete Jacobian and timing derivative.
- **486 native calls maximum**, four total numerical threads, no retries.
- At most three within-offset saved residual comparisons.
- One software-qualification batch, eleven tests, no original reads or observed
  calls, at most 256 software callbacks and 120 seconds.

Sources, input artifacts, original hashes, numerical environment, task identities
and exact anchors are frozen before launch. Charge every start and call before
execution; interrupted calls remain charged. Resume only unchanged unfinished
work and never retry a charged identity. Completed work cannot restart or reuse
unused allowance. The original completed studies remain unchanged.

## Checks and interpretation

Use the qualified fixed-time adapter and existing bounded trust solver. Preserve
the measurements, original physical bounds, initialization, nominal clock,
unsubtracted-increment hypothesis, receiver weights and stopping tolerances.
Only the timing coordinate is removed from the conditional optimization; its
full derivative remains in the saved final artifact. Fresh final cost must agree
within relative 1e-8. Report both starting solutions at every point, including
failures. Apply the existing relative 1e-6 cost and 1 cm track-RMS repeat limits
to the two fits at each identical time.

Software tests exercise the actual receipt ledger through fitting and final
diagnostics, including a charged final failure. They also reject incomplete,
failed or changed endpoint evidence and verify exact interpolation and limits.

Publish all five offsets as a table and CSV, combining the three interior
offsets with the two verified endpoints. This is a coarse nonlinear diagnostic,
not a global optimization proof. Do not select a favorable model or relax the
full free-time gate. The profile does not change the 49 globe / zero flat / four
unresolved disposition. A revised free-time candidate needs its own controls
and separately frozen finite qualification after this profile is interpreted.
