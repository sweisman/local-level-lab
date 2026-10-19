# Timing derivative and path results

Completed **29 fixed evaluations in 5.28 minutes**, with zero optimizer starts. All primary and repeat centers reproduced exactly. No fit, repeat or scientific labels changed.

## Independent timing derivatives

The analytic timing column is compared with symmetric one-microsecond residual differences. Errors below are relative vector-norm discrepancies, not statistical uncertainty. Distance to the nearest nominal integration boundary is reported separately.

| Processing / endpoint | Relative derivative error | Nearest clock boundary (µs) | Perturbation crosses boundary? |
|---|---:|---:|---|
| unsubtracted / primary | 8.30245e-05 | 709.089 | no |
| unsubtracted / repeat | 7.76991e-05 | 1750.231 | no |
| profiled_removal / primary | 8.7083e-05 | 709.088 | no |
| profiled_removal / repeat | 7.86739e-05 | 1750.231 | no |
| IMU8 control / primary | 0.000149568 | 1368.381 | no |

## Full-vector path

Every nuisance coordinate moves together along the straight line between saved endpoints. These are fixed-point costs, not reoptimized timing-profile costs. The timing column gives its parameter value relative to the recorded receiver times.

| Fraction from primary to repeat | Timing (ms) | Unsubtracted cost | Profiled-removal cost |
|---:|---:|---:|---:|
| 0.000 | -84.227688 | 5.564176204 | 5.564176206 |
| 0.125 | -86.597545 | 5.564913593 | 5.564913591 |
| 0.250 | -88.967402 | 5.566181738 | 5.566181738 |
| 0.375 | -91.337260 | 5.567721408 | 5.567721407 |
| 0.500 | -93.707117 | 5.569500712 | 5.569500713 |
| 0.625 | -96.076974 | 5.571065595 | 5.571065594 |
| 0.750 | -98.446831 | 5.572399014 | 5.572399015 |
| 0.875 | -100.816688 | 5.573230579 | 5.573230577 |
| 1.000 | -103.186546 | 5.573073571 | 5.573073571 |

## Interpretation

The five derivative comparisons differ by **0.0078–0.0150%** in vector norm. No perturbation crosses a nominal integration boundary. This finds no gross timing-derivative fault. It does not certify the accuracy of a nearly cancelled objective gradient or prove either endpoint is globally optimal.

Both processing cases give almost identical sampled costs. The path rises from the primary toward the repeat, reaches a sampled high point just before the repeat, then falls slightly. This is consistent with distinct locally stationary solutions connected through coupled timing/calibration directions. The path was not reoptimized at intermediate times, so it is not a minimized timing profile.

No failed repeat passes from these points. The horizontal-only fits retain their large unscored height errors; the original full-position **53 globe / zero flat / zero unresolved** results are unchanged. The next task is known-answer qualification of a deterministic multi-start method before any new observed fits.

[Recovery qualification plan](NEXT_PLAN.md) · [All saved point metrics](README.md) · [Frozen scope](PLAN.md) · [Preceding diagnosis](../ilvis0-horizontal-repeat-probes-20261019/INTERPRETATION.md).
