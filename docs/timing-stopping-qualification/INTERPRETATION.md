# Timing-aware stopping passes its analytical qualification

All **32 complete fits** reach their independently stated known-answer costs
and predictions. All **eight direct controls** behave as specified. Predictions
from the four declared starts agree for each of the eight objective families.

The run takes **26 seconds** on one numerical thread. It uses 1,008 analytical
residual evaluations and 905 bounded linear operations, within the frozen
limits of 6,688 and 20,000. It makes no native propagation calls and reads no
aircraft observations. The source-bound preflight suite passes 161 tests.

## What this checks

| Objective family | Complete fits | What it tests |
|---|---:|---|
| Interior optimum | 4/4 | A solution inside the allowed parameter range. |
| Physical-bound optimum | 4/4 | A valid solution at a parameter limit. |
| Nonlinear optimum | 4/4 | Recovery through a curved objective. |
| Curved redundant problem | 4/4 | Stable predictions despite nonunique parameters. |
| Timing kink at zero | 4/4 | A minimum where the timing slope changes. |
| Shifted timing kink | 4/4 | The same issue away from zero. |
| Smooth timing optimum | 4/4 | Ordinary timing estimation remains correct. |
| Redundant timing problem with 27 coordinates | 4/4 | Complete nuisance freedom is retained. |

Two direct checks accept valid kink minima. Two reject points that are not
minima. The remaining checks retain rejection for excessive physical change,
nonrepeatable calculations and an exhausted work budget. A sharp minimum also
remains unresolved when it fails the original stationarity limit: that extra
conservative requirement has not been removed.

The audit recomputes costs, prediction errors and verification metrics from
the saved traces. Every start and work journal is retained. Rejected controls
are successful tests of rejection; they are not converged model fits.

## What comes next

This qualifies the analytical fitting path. A
[separate native qualification](../TIMING_OPTIMIZER_NATIVE_PLAN.md) must check
the same method with the unchanged physical integrator and noise calculation.
It starts with four existing exposed generated-data cases, including the two
previous numerical failures. It does not reopen calibration or supply a
statistical confidence threshold.

No previous convergence label or airborne finding changes. The 53-stretch
comparison and protected confirmation groups remain separate from these
software controls.

[Every result](results.csv) · [Start comparisons](pairs.csv) ·
[Frozen plan](PLAN.md) · [Reproduction record](README.md) ·
[Next analyses](../NEXT_STEPS.md).
