# Small coordinate changes survive compensated accumulation

Completed 18/18 coordinate controls; compensation qualified: True.
These are arithmetic controls with known answers, not flight measurements.

| Control | Arithmetic | Precision check | Largest relative difference error |
|---|---|---|---:|
| north-small-baseline | baseline | True | 2.13908e-16 |
| north-small-previous | previous | True | 2.13908e-16 |
| north-small-compensated | compensated | True | 2.13908e-16 |
| north-large-baseline | baseline | False | 1 |
| north-large-previous | previous | False | 1 |
| north-large-compensated | compensated | True | 2.13908e-16 |
| east-small-baseline | baseline | True | 2.96376e-09 |
| east-small-previous | previous | True | 2.96376e-09 |
| east-small-compensated | compensated | True | 2.96376e-09 |
| east-large-baseline | baseline | False | 1 |
| east-large-previous | previous | True | 2.96376e-09 |
| east-large-compensated | compensated | True | 2.96376e-09 |
| height-small-baseline | baseline | True | 1.61392e-10 |
| height-small-previous | previous | True | 1.61392e-10 |
| height-small-compensated | compensated | True | 1.61392e-10 |
| height-large-baseline | baseline | False | 0.00997258 |
| height-large-previous | previous | False | 0.00997258 |
| height-large-compensated | compensated | True | 1.61392e-10 |

All 26 nuisance columns remain. A failed precision comparison stays failed.
The report does not qualify a solver, a saved-data fit or an uncertainty threshold.

[Results CSV](results.csv) · [Frozen plan](PLAN.md) · [Next analyses](../NEXT_STEPS.md).
