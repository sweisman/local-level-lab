# Independent bounded-optimizer forecast control

**6/6** generated fixtures passed the preregistered numerical agreement gate. 24/24 fits passed their unchanged final stopping checks; 24/24 passed the separate generated physical screen; 0 had technical failures.

| Generated model | Clock | Numerical stops | Physical screen | Largest later-path spread | Training cost range |
|---|---|---:|---:|---:|---:|
| sphere_rotating | header_elapsed | 4/4 | 4/4 | 8.07e-07 m | 1.7e-10 |
| sphere_rotating | nominal_200Hz | 4/4 | 4/4 | 3.12e-06 m | 2.78e-10 |
| sphere_still | header_elapsed | 4/4 | 4/4 | 8.05e-06 m | 2.58e-10 |
| sphere_still | nominal_200Hz | 4/4 | 4/4 | 9.55e-06 m | 3.21e-10 |
| flat_still | header_elapsed | 4/4 | 4/4 | 5.06e-05 m | 1.02e-10 |
| flat_still | nominal_200Hz | 4/4 | 4/4 | 5.53e-06 m | 2.04e-10 |

Largest later RMS error against generated truth: 1.22 m horizontal and 1.77 m in height.

SciPy TRF is a different bounded optimizer from the existing trust-region method. Each fit uses 39 earlier receiver reports and predicts 20 withheld reports. The six histories have distinct noise seeds but use one generator family. Agreement here qualifies only this generated numerical control; it cannot establish a global optimum, aircraft prediction coverage or a scientific decision. The 50 original nonpassing aircraft fit labels are unchanged.

[Frozen plan](INDEPENDENT_SOLVER_PLAN.md) · [All fit outcomes](independent-solver-tasks.csv) · [Earlier scope correction](SOLVER_INDEPENDENCE_ERRATUM.md)
