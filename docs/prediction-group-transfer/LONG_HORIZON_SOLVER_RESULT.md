# Longer generated solver confirmation

**6/6** generated histories passed the preregistered numerical gate. 24/24 fits passed stopping, 24/24 passed the separate generated physical screen, and 0 had technical failures.

| Generated model | Clock | Numerical stops | Physical screen | Largest later-path spread | Training cost range |
|---|---|---:|---:|---:|---:|
| sphere_rotating | header_elapsed | 4/4 | 4/4 | 8.28e-08 m | 1.47e-10 |
| sphere_rotating | nominal_200Hz | 4/4 | 4/4 | 1.91e-06 m | 3.75e-11 |
| sphere_still | header_elapsed | 4/4 | 4/4 | 7.03e-07 m | 9.28e-10 |
| sphere_still | nominal_200Hz | 4/4 | 4/4 | 9.91e-07 m | 5.58e-11 |
| flat_still | header_elapsed | 4/4 | 4/4 | 5.06e-05 m | 1.45e-10 |
| flat_still | nominal_200Hz | 4/4 | 4/4 | 3e-07 m | 2.53e-10 |

Largest later RMS error against generated truth: 5.29 m horizontal and 1.04 m in height.

Each fit uses 79 earlier receiver reports and predicts 40 withheld reports over a 120-second generated history. The six histories use distinct noise seeds but one declared generator family. Close solver paths and training costs qualify a numerical method on these inputs; they do not establish aircraft prediction coverage. The original 50 nonpassing aircraft labels and protected ESA flights are unchanged.

[Frozen plan](LONG_HORIZON_SOLVER_PLAN.md) · [All fit outcomes](long-solver-tasks.csv)
