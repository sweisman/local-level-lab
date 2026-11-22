# Allowing persistent errors improves the forecasts' error scores

Allowing forecast errors to persist after turns improved the joint log score
on **all eight** omitted windows. It still left only **two of eight** inside
the fixed error reference. Neither version passed the development gate.

| Correlation rule | Total omitted negative log score | Windows inside the reference |
|---|---:|---:|
| Saved diagonal scales | −10,725.40 | 2/8 |
| Common persistence | −11,608.88 | 1/8 |
| Persistence linked to turn activity | −11,739.68 | 2/8 |

Lower scores are better. Both inertial error descriptions agree to the
precision shown. The common rule selected two or four seconds in every fold.
The turn-linked rule selected two seconds for quiet flight and **64 seconds**
for the active component in every fold. That is the largest setting tested,
so the result leaves the duration of the longer memory open.

The hardest turn's squared error score fell from 474.73 to 254.58 against
a working reference of 290.94–437.69. The revised rule put five windows
below the reference and one above. The remaining high score was on a steady
window. The diagonal variances were learned before adding persistence and
stayed fixed here. The large gain supports looking at persistence and variance
together. It gives no calibrated error range for another flight.

All eight tasks completed in 15.16 seconds on two one-thread workers. Eleven
software checks passed, including comparison with a dense covariance on an
irregular clock. The run used 912 charged operations, zero new trajectory fits,
and no original recordings or reserved flights.

[Frozen method](ESA_INNOVATION_PERSISTENCE_PLAN.md) ·
[All memory settings and scores](esa-innovation-persistence-result.json) ·
[Verified run evidence](esa-innovation-persistence-evidence/README.md)
