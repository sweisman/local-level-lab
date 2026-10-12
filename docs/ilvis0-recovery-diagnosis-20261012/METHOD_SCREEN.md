# Bounded-method software screen

This compares two actual optimization strategies on **60 small software starts**:
TRF (the completed trial's method) and dogbox (a rectangular trust-region method).
It reads no archival observations and performs no native integrations. Both use
the same original parameter box, Jacobian scaling, 600-evaluation ceiling, fresh
gradient check and unchanged cost/residual stability checks.

| Known-answer control | TRF | Dogbox |
|---|---:|---:|
| interior | 3/3 | 3/3 |
| boundary | 3/3 | 3/3 |
| redundant | 3/3 | 3/3 |
| scaled | 3/3 | 3/3 |
| nonlinear | 3/3 | 3/3 |
| gain_offset | 3/3 | 3/3 |
| mixed_interior | 3/3 | 3/3 |
| mixed_boundary | 3/3 | 3/3 |
| coupled_interior | 3/3 | 3/3 |
| coupled_boundary | 2/3 | 3/3 |
| **Total** | **29/30** | **30/30** |

Each control has three predetermined starts. The last two controls have 27 coupled
parameters, a 100-million-to-one singular-value ratio, and a near-boundary start.
Known prediction and objective recovery are checked separately from numerical
termination. Unique parameters are checked only where the equations identify them.
Both strategies call the real SciPy optimizer; temporary dispatch leaves the
completed trial's source unchanged.

## Failed software checks

- `trf::coupled_boundary::2`: 29 evaluations; known answer passed; final checks failed; linear_correction_not_stable.

## What this establishes

This is a screen, **not qualification for the airborne archive**. The controls
demonstrate behavior on specified equations, not the cause of a particular saved
flight's stall. Complete observed Jacobians and rejected-step traces were not saved
in the recovery trial. A new observed diagnostic needs a separate source freeze
and finite allowance. Neither a successful software test nor an unused completed
allowance permits replaying the 41 unfinished stretches.

Run `screen_methods.py --render-only` to regenerate this page from saved results.
Running it without that flag performs this small software screen again; it never
starts archival fits. Input/source/environment hashes are in the screen receipt.
