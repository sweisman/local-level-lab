# Full-calibration generated solver pilot

The study completed 4 fixed task identities. 4/4 fits passed numerical stopping, 4/4 passed the separately declared physical accuracy screen, and 0 had technical failures.

Largest later-path separation among the four saved fits: 3.42e-07 m.

| Solver | Start | Numerical stop | Physical screen | Training cost | Later horizontal RMS | Later height RMS |
|---|---:|---:|---:|---:|---:|---:|
| near_zero | 0 | yes | yes | 94.6123 | 0.321 m | 1.31 m |
| near_zero | 1 | yes | yes | 94.6123 | 0.321 m | 1.31 m |
| trust_v2 | 0 | yes | yes | 94.6123 | 0.321 m | 1.31 m |
| trust_v2 | 1 | yes | yes | 94.6123 | 0.321 m | 1.31 m |

All four tasks use the same independently generated noisy flight, full 26-parameter calibration box and earlier-only receiver cut. This is a development diagnostic: solver agreement is not aircraft accuracy. The physical screen here compares generated paths with known truth; a small training cost is not a withheld-position accuracy claim. Observed aircraft fits and the reserved ESA confirmation groups remain unchanged.

[Frozen pilot plan](FULL_CALIBRATION_SOLVER_NEXT.md) · [All task outcomes](fullcal-solver-pilot-tasks.csv)
