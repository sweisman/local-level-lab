# Completing the ESA error fits leaves the same two misses

All eight donor fits met the projected-gradient stopping check. The largest
improvement in the donor loss was 0.00000055. The largest change in an omitted
window’s log score was 0.0027. Both input conventions still put six of eight
windows inside the original error reference.

| Window | Position in the reference | Score before | Score after |
| --- | --- | ---: | ---: |
| 21856, steady | Above the upper limit of 437.69 | 491.84 | 491.84 |
| 33796, turn | Below the lower limit of 290.94 | 276.65 | 276.65 |

The table shows squared standardized errors for the point input. The
increment input gives the same values at this precision. The results show
that unfinished optimization did not explain the misses. The error model
remains in development. Check whether the available steady and turning
windows can explain the opposite misses before adding more fit parameters.

The runner completed all eight tasks in 13.7 seconds with 321 charged calls.
The original capped fits are preserved. No new aircraft trajectories were
fitted, and no reserved flights were opened.

- [Frozen plan](ESA_JOINT_PERSISTENCE_ANALYTIC_PLAN.md)
- [Fit and forecast scores](esa-persistence-analytic-result.json)
- [Verified execution and reproduction](esa-persistence-analytic-evidence/README.md)
