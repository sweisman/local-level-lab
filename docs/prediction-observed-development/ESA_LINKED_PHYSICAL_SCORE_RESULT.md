# Linked calibration produces smaller forecast changes on the saved ESA map

The [linked search](ESA_LINKED_PHYSICAL_SCORE_PLAN.md) derived all 24
shared terms from the same 27 physical parameters at every proposed
point. All 12 tasks and 120 point checks completed.

| Assumed earlier unshared error norm per candidate | Largest verified globe movement | Largest verified disc movement | Combined movement |
| ---: | ---: | ---: | ---: |
| 0 | 0.211 | 0.221 | 0.432 |
| 0.1 | 6.024 | 6.519 | 12.542 |

The movements are in standardized units toward the other forecast.
The nominal separation is **25.41 units**. With the 0.1 allowance,
the strongest checked linked examples move about half that distance.
The [relaxed disc example](ESA_ATTITUDE_SURVIVOR_SCORE_RESULT.md)
moved 31.86 units but failed earlier GPS once its shared terms
came from one calibration.

Six of the 12 numerical searches reported convergence. Each reported
movement comes from a point verified against the earlier loss limit
for its declared allowance. These are attainable examples, so they
provide lower bounds on the greatest possible movement. The global
upper bound from the inequalities remains 54.00 units.

The next check will replay the strongest accepted points through the
full integrating model. It will measure how much error the saved
linked map left out and whether the points still fit the earlier GPS
without the hypothetical allowance. The independent aircraft study
remains unopened.

[Full integrating-model replay](ESA_LINKED_PHYSICAL_REPLAY_RESULT.md).

[Sealed checked points and search inputs](esa-linked-physical-score-evidence/README.md).
