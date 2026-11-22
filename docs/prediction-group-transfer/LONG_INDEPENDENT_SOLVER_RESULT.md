# Longer independent-optimizer forecast control

**6/6** generated histories passed the preregistered numerical agreement gate. 24/24 fits passed their unchanged final stopping checks; 24/24 passed the separate generated physical screen; 0 had technical failures.

| Generated model | Clock | Numerical stops | Physical screen | Largest later-path spread | Training cost range |
|---|---|---:|---:|---:|---:|
| sphere_rotating | header_elapsed | 4/4 | 4/4 | 4.97e-06 m | 2.92e-10 |
| sphere_rotating | nominal_200Hz | 4/4 | 4/4 | 2.74e-07 m | 2.42e-10 |
| sphere_still | header_elapsed | 4/4 | 4/4 | 1.1e-05 m | 5.03e-10 |
| sphere_still | nominal_200Hz | 4/4 | 4/4 | 2.43e-05 m | 3.09e-10 |
| flat_still | header_elapsed | 4/4 | 4/4 | 3.67e-05 m | 3.31e-10 |
| flat_still | nominal_200Hz | 4/4 | 4/4 | 9.06e-06 m | 3.52e-10 |

Largest later RMS error against generated truth: 4.12 m horizontal and 2.37 m in height.

SciPy TRF and the custom trust-region solver are separate bounded optimizers. Each fit uses 79 earlier receiver reports to predict 40 withheld reports over a 120-second generated history. The six histories have distinct noise seeds but one generator family. This numerical control cannot establish a global optimum, aircraft prediction coverage or a scientific decision. The original 50 nonpassing aircraft fit labels remain unchanged. A host interruption left two charged starts unfinished; the original allowance is sealed and the four missing identities were completed under a separately qualified finite recovery. No completed task was repeated.

[Frozen plan](LONG_INDEPENDENT_SOLVER_PLAN.md) · [All fit outcomes](long-independent-solver-tasks.csv) · [Earlier scope correction](SOLVER_INDEPENDENCE_ERRATUM.md)
