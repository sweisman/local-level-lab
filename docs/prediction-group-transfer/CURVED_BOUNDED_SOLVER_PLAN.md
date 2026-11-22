# Bounded solver check with exact optima

Compare the existing bounded trust-region and SciPy TRF methods with an
L-BFGS-B alternative that evaluates the same sum of squares relative to its
starting value and uses the analytic gradient. Keep the fresh stationarity,
cost and actual-position checks identical. Run no aircraft fit.

Each generated residual vector is `[102 + q*d², 20*(y - b - c*d²), s*d]`,
where `d = x - 0.25`. All coordinates are bounded by ±1. The exact optimum
is `(0.25, clip(b, -1, 1))`. The first term grows strictly with `d²`. The
second term has its global minimum at `d=0` after minimizing over `y` when
`b` is within the box or when the bend points farther out of the box. The
third term also has its minimum at `d=0`. These facts give an independent
optimum for each case.

Use four cases and two matched starts `(-0.65, -0.55)` and `(0.75, 0.60)`.
Use the residual changes directly as the three metre-scale position changes
in the unchanged fresh-position check.

| Case | q | b | c | s |
| --- | ---: | ---: | ---: | ---: |
| Linear control | 0 | 0.20 | 0 | 0.50 |
| Curved interior | 0.05 | 0.20 | 0.08 | 0.002 |
| Curved upper face | 0.05 | 1.06 | 0.08 | 0.002 |
| Curved lower face | 0.05 | −1.06 | −0.08 | 0.002 |

Count all objective and derivative calls, with up to 200 calls per fit,
24 fit tasks, one thread and a 60-second wall limit. A fit must pass the
unchanged stopping check, have absolute objective gap at most 10⁻⁷ and
maximum coordinate error at most 10⁻⁴. Preserve each disposition, including
any standalone solver success flag. This qualifies only these generated
controls. No observed failure changes label. No reserved group is used.
