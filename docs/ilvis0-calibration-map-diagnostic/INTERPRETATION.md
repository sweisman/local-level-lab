# Some allowed error combinations are not physical calibrations

**All 36 checked extremes fail** when their common-error terms are recomputed
from a single calibration. The known generated controls reproduce exactly in
all six groups. No witness collapsed to the known answer during exact repair.

The current prediction calculation contains 27 physical calibration values and
24 derived error terms. Its outer region lets those terms vary more independently
than a real calibration does. Necessary matrix relationships did little to remove
that freedom. This diagnostic now tests the complete calibration relationship.

Recomputing it changes the saved affine future position by as much as 81.86 m.
The largest individual block changes are 72.14 m from acceleration, 12.46 m from
the lever arm, 3.63 m from velocity/clock coupling and 0.22 m from the force matrix.
Binary conversion contributes less than 7e-15 m. Block changes can cancel; these
are not percentages of evidence or errors measured on an aircraft.

The result supports replacing independent error variables with a coupled
calibration treatment. It does **not** supply a narrower certified interval:
rejecting 36 proposed extremes does not exclude every other point. The existing
prediction gate remains unmet, and the 53 aircraft comparisons are unchanged.

The six-case run took 13.2 seconds. It used all 36 LP proposals and 42 map calls,
plus 142,878 of 246,000 allowed scalar checks. Reservations reconcile with the
sealed results. There were no new native trajectories, bounds, original-aircraft
reads or observed fits. All allowances are now closed.

[Results](README.md) · [Frozen scope](PLAN.md) · [Next method](NEXT_PLAN.md).
