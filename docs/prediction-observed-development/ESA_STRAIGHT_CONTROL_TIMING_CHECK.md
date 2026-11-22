# Check whether the turn timing matters

The actual turn allowance is zero whenever the instrument records
zero angular exposure. A steady-course control could therefore show
zero score change by construction.

Keep that result and also score each control using its matched turn's
exposure, aligned by forecast report number. Use the archived turn
forecast for the same inertial error description. The control keeps its
own predicted path, native uncertainty and GPS query times. Only the
turn exposure changes. Verify the donor seal and construct the modified
record before opening the later control positions. Confirm that scores
for the two models without a turn allowance are identical.

Report the gains from the reassigned exposure alongside the actual
turn and control scores. This checks whether a turn-shaped allowance
would help on a different part of the same flight. It uses the same
positions and adds at most eight scores, with no additional fits.

Follow the [release commands](ESA_STRAIGHT_CONTROL_RELEASE_PLAN.md).
The updated test report is
`esa-straight-control-forecast-timing-tests.xml` in the same directory.
