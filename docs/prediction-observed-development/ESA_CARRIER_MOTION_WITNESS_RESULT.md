# The smooth-path search found partial explanations for the ESA score gap

The checked paths account for **47.7%–64.9%** of the two-minute ESA
development score gap. All stayed within the example limits for
position at the anchors, trajectory error acceleration and range error.
The search reached its iteration limit in every case, so the existence
of a path that spans the whole gap remains open.

| Maximum starting tilt | Share of gap reached within the limits | Largest anchor error on any coordinate | Range error in ground-covered directions |
| --- | ---: | ---: | ---: |
| Full satellite set | 47.7% | 0.7 cm | 0.983 mm RMS |
| 0° screen | 55.1% | 15.3 cm | 0.359 mm RMS |
| 5° screen | 59.6% | 4.8 cm | 0.355 mm RMS |
| 10° screen | 64.9% | 7.0 cm | 0.346 mm RMS |

For each case, the calculation scaled the optimizer's returned path
to meet the declared error limits. It then checked the path directly
using the original score times and a continuous cubic curve. It
checked range error separately inside and outside ground coverage,
including an allowance for nonlinear range geometry. Some unscaled
paths exceeded the score gap but also exceeded the acceleration limit.
Only the scaled paths in the table met all limits.

The paths demonstrate what errors could do under the stated model.
They supply no estimate of the aircraft's actual errors. The separate
[range and anchor check](ESA_CARRIER_REWEIGHTED_BUDGET_RESULT.md) leaves
no guaranteed margin under the example in the three screened cases.
Together these results leave a substantial gap between what the
current upper bounds allow and what the search has demonstrated.

The [continuous bound](ESA_CARRIER_CONTINUOUS_BOUND_RESULT.md) later
excluded a complete trajectory explanation for the full satellite set
under the example limits. All three screened cases remained open.

One task completed 245 charged checks. All four solver stops were
preserved. Ten focused tests passed. There were zero new model fits
and zero reserved-flight reads.

[Frozen plan](ESA_CARRIER_MOTION_WITNESS_PLAN.md) ·
[Saved paths, checks and completion receipt](esa-carrier-motion-witness-result.json)
