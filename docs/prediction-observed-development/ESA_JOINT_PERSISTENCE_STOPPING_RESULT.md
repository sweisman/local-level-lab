# Checking where the ESA error fits stopped

All eight saved donor scores reproduced to within 0.000000000002.
Two sizes of numerical probes checked the analytic derivatives. At the
smaller step, the largest discrepancy was 0.00000045 per log unit.

| Forecast pair | Largest feasible slope, increment input | Largest feasible slope, point input |
| --- | ---: | ---: |
| 22936 | 0.00385 | 0.00394 |
| 33796 | 0.00831 | 0.00859 |
| 37516 | 0.01002 | 0.01002 |
| 41116 | 0.00872 | 0.00871 |

Every saved setting still has a measurable downhill direction within the
original bounds. The slopes alone cannot say how far the solution would
move or whether that would bring the two outlying windows inside the error
reference. The original evaluation-limit outcomes stand. The next bounded
comparison can use these derivatives to test that directly before changing
the error model.

The checks used six donor windows per fit. The runner completed eight of
eight checks in 9.3 seconds with 256 charged calls and no new fits. It did
not score the omitted windows or access reserved flights.

- [Frozen plan](ESA_JOINT_PERSISTENCE_STOPPING_PLAN.md)
- [Gradients, bounds and score replays](esa-persistence-stopping-result.json)
- [Verified execution and reproduction](esa-persistence-stopping-evidence/README.md)
