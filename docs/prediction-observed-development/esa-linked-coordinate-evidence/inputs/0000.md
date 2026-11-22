# Contract the surviving ESA calibration ranges with the archived constraints

The [latest score-direction check](ESA_LINKED_LOSS_TANGENTS_RESULT.md)
left a 53.20-unit upper bound against a 25.41-unit forecast gap. Keep all
eleven surviving ranges, earlier exclusions, original earlier loss cap of
0.01 and zero unshared error. Check whether the earlier constraints already
give smaller ranges for any of the 27 physical calibration coordinates.

Use all 60 columns in the saved static inequalities. Add five necessary
training inequalities to each child, using the nominal residual and four
archived loss or score directions. Enclose each projected coefficient by
outward arithmetic. Round its midpoint to the proposed affine coefficient
and add the worst rounding or enclosure discrepancy over the original box
to the right-hand side. Keep all 27 physical and 33 shared or lifted terms
in the coordinate projection.

For each physical coordinate, propose a linear-program bound in both
directions. Accept only a nonnegative dual bound verified by exact arithmetic
and the independent evaluator. An unavailable numeric proposal retains the
original endpoint. Check that every saved feasible point remains in the
contracted box. Replay the archived parent and two child score directions
on the narrower linked physical map. Use the minimum verified bound or
keep the previous bound. Retain the previous bound on any failed range.

Freeze eleven tasks on two one-thread workers with a 300-second cooperative
limit. Each task allows five necessary inequalities, 54 coordinate proposals
with their three exact checks each, and three linked score bounds. No new
trajectory fit, model change, later position read or reserved flight is
part of this check. A smaller static bound leaves the full integration
remainder and aircraft error coverage open.
