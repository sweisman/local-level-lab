# Size of a shared motion error that would shift the fixed shape score

The [in-flight Doppler comparison](ESA_DOPPLER_CONTRAST_RESULT.md)
measures how the fixed score responds to differences among three paths
from one aircraft antenna. A displacement error shared by all three
leaves their pairwise differences unchanged.

Use the original, certified affine score and the same 120 later
report times. Set displacement and its rate to zero at the last
earlier report and at the last later report. Allow a shared error in
between. Find the minimum time-averaged squared norm of the three
coordinate accelerations needed to produce a score shift equal to the
published lower gap. The acceleration is the second time derivative
of position error in the score's coordinate metric. It does not
represent a measured accelerometer bias.

For a unit acceleration at time `t`, the displacement at a later
report `s` grows with `s - t`. The score sensitivity to acceleration
is therefore a piecewise linear function. Remove its constant and
linear time components to enforce zero final velocity and displacement.
Scale the remaining function to reach the gap. Its squared integral
gives a lower bound by the Cauchy–Schwarz inequality, and the scaled
function attains the bound. Integrate it forward independently and
verify both endpoint conditions and the signed score in exact
rational arithmetic.

Use one worker and one numerical thread, two bounded operations and
241 steps across the 121 knots and 120 intervals. The wall limit is
180 seconds and technical recovery uses the existing finite
allowance. Read only the saved score, report times and gap. No receiver
outcomes, fits, new forecasts or reserved flights are needed.

The result gives a sensitivity scale under the frozen score. It does
not establish how large an error the receiver actually has, whether
such a pattern could occur with the same raw signals, or whether it
would change an aircraft model decision after refitting.
