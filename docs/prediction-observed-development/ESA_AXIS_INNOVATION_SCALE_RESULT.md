# Separate quiet scales improve ESA scores while most windows still miss

Giving north, east and height innovation slots separate quiet scales improved
the held-out log score on **all eight windows** compared with the earlier
shared motion rule. It put **two of eight windows** inside the error reference,
up from one. Neither new rule passed the development screen, which requires
all eight windows inside the reference as well as a better joint score.

| Rule | Total held-out negative log score | Windows inside the reference |
|---|---:|---:|
| Original covariance | −9,562 | 1/8 |
| Shared quiet and motion scales | −10,143 | 1/8 |
| Separate quiet scales, shared motion scale | −10,725 | 2/8 |
| Separate quiet and motion scales | −10,683 | 2/8 |

Lower log scores are better. In all four omitted pairs, the best rule chose
the same quiet multiplier of 0.135 in the north and east slots. The height
multiplier was 0.368 in one pair and 1.0 in the others. These are slots in an
ordered covariance factor. They cannot identify separate GPS or inertial error
sources. The forecasts remained fixed.

On the hardest turn, the mean squared standardized error remained 1.32
under the best rule, above the reference centered on one. Giving the motion
scales their own slots raised it to 1.67. On the hardest steady leg the best
rule reduced it from 4.59 to 2.06, still outside the reference. Every scale
selection used the six other windows. Both inertial error descriptions give
the same results to the displayed precision. The eight windows come from
one development flight. The results do not establish coverage on other flights.

All eight folds passed the software checks in 34 seconds. The new score
matched a dense covariance in the known-answer test and reproduced the
archived scores when the scales were shared. No trajectory was refitted
and no reserved flight was opened.

[Frozen method](ESA_AXIS_INNOVATION_SCALE_PLAN.md) ·
[All scale and forecast-error results](esa-axis-innovation-scale-result.json) ·
[Verified run evidence](esa-axis-innovation-scale-evidence/README.md)
