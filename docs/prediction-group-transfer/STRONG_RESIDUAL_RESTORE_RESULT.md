# Restoring the strong residual passes all eight analytic-curvature controls

The correction recovered both weak-direction starts when the generated
problem supplied its exact curvature. That arm passed **8/8** under
the original fresh convergence and accuracy requirements. The
finite-difference arm passed **6/8**. It moved closer to both weak
solutions and still failed their fresh checks after 40 evaluations each.

| Generated problem | Analytic curvature | Finite differences |
| --- | ---: | ---: |
| Curved interior | 2/2 | 2/2 |
| Upper bound | 2/2 | 2/2 |
| Lower bound | 2/2 | 2/2 |
| Weak direction | 2/2 | 0/2 |

The restored analytic weak starts finished in **17 and 15** evaluations.
The finite-difference version reduced the maximum parameter errors from
about 0.734 and 0.476 to 0.000209 and 0.000000657. These are errors
in normalized solver parameters. The second result is within the
parameter tolerance and still fails the fresh-position check.

The two arms accepted all 14 measured corrections to rejected trials.
The 16 starts used 356 evaluations. Ten focused software checks passed.
The analytic pass establishes that a step can follow the coupled weak
direction and satisfy the original gate when the curvature is known.
Aircraft fitting does not supply that analytic curvature. A cheaper
derivative estimate still needs to pass the weak controls and a
separate generated flight-scale test before use on an observed fit.

Previous dispositions and the default solver remain unchanged.
No aircraft fit ran and no reserved data was opened.

[Frozen plan](STRONG_RESIDUAL_RESTORE_PLAN.md) ·
[Verified dispositions and completion record](strong-residual-restore-result.json)
