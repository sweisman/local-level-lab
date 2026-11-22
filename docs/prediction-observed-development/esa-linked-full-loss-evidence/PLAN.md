# Apply the full earlier-fit loss to the ESA calibration ranges

Use the eleven surviving ranges from the [graph-cut check](ESA_LINKED_GRAPH_CUTS_RESULT.md).
Keep all 60 coordinates, the 0.01 increase allowed in earlier squared loss,
the previous static constraints and the checked graph and earlier-loss cuts.
Keep the 25.41-unit forecast gap and every earlier witness and exclusion.

An earlier full-loss solver stalled on most boxes. Here, first select a
direction in which the archived earlier residual changes little across each
box. Use the saved receiver operator to enclose its range with outward
arithmetic. Subtract only the squared energy guaranteed along that direction.
First minimize the squared residual in the perpendicular space. Then propose
the largest forecast change under its remaining loss limit. Use bound-scaled
coordinates and analytic derivatives. Limit each proposal to 128 distinct
residual evaluations.

For either point, take its calculated earlier residual direction and remove
its component along the energy already budgeted. Bound the perpendicular
part on the remaining residual ball. Use the saved earlier operator and exact
projection arithmetic to enclose the coefficient range. Add the necessary linear
constraint and use the two existing exact certificate calculations to bound
the forecast score. If a projection alone contradicts the whole linear region,
require a separate exact lower certificate before excluding the range. Check
all feasible witnesses. A numerical stopping status never certifies anything.

Retain the best checked bound, including the previous one. Report which ranges
shrink or are excluded and whether the combined bound falls below the
forecast gap. This still bounds the archived affine prediction and its
calibration representation. The nonlinear integration remainder and real
aircraft uncertainty need their own checks.

Freeze eleven tasks, three one-thread workers, 360 seconds and two numerical
proposals, three projection checks and at most four linear programs per range.
Bind the tested shared recovery policy with a 600-second recovery allowance.
Run zero new trajectory fits or integrations. Use no later receiver positions
or reserved recordings.
