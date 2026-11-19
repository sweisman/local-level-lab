# The saved calibration inequalities still allow enough movement to erase the ESA forecast difference

The direct calculation narrowed the numerical uncertainty. For each
candidate, feasible points and certified upper bounds put the largest
forecast movement within about **0.04 standardized units**. The permitted
movement still exceeds the **25.41-unit** difference between the saved
forecasts.

| Assumed earlier unshared error norm per candidate | Globe movement | Disc movement | Combined movement |
| ---: | ---: | ---: | ---: |
| 0 | 39.680–39.721 | 40.193–40.234 | 79.873–79.954 |
| 0.1 | 39.785–39.826 | 40.345–40.386 | 80.130–80.211 |

The lower endpoints come from points that passed the earlier GPS loss
check and all 132 static inequalities. The upper endpoints come from
independently checked certificates. Thus, even the current constraints
allow enough movement to erase the forecast difference in this saved
calibration calculation. The feasible points can still violate the
exact physical calibration map.

All eight solver starts completed in the
[frozen check](ESA_DIRECT_TRAINING_SCORE_PLAN.md). The original proposed
points missed at least one rounded static inequality. Moving each
proposal 0.1% of the way toward a saved feasible point allowed it to
pass the exact checks. No new trajectory fits or later positions were
used.

The next step is to tighten the physical relationship between the
acceleration and force terms, which accounted for nearly all of the
disagreement in the [saved calibration examples](ESA_COUPLED_TRAINING_SCORE_RESULT.md).
The aircraft error model and independent confirmation remain open.

[Sealed inputs, proposed points and certificates](esa-direct-training-score-evidence/README.md).
