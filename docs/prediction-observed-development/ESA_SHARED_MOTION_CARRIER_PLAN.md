# Test the shared displacement against the archived satellite clock change

The [endpoint-preserving example](ESA_SHARED_MOTION_GAP_RESULT.md)
is a displacement in the score's coordinates. This follow-up calculates
the carrier range change that would have to cancel that displacement so
the original observations would still fit. It also checks whether the
archived broadcast-to-final satellite clock correction has that pattern.

Use the 240 consecutive half-second pairs, satellite masks and unshifted
positions from the [later carrier replay](ESA_CARRIER_PHASE_LATER_RESULT.md).
At each measured time, evaluate the saved displacement by integrating its
linear acceleration between knots. Use the certified coordinate metric
and the original clock origin. Interpolate no measured sample. Compute
the change in geometric range, including the carrier model's Sagnac
term, at both shifted endpoints while preserving the original satellite
transmit times. Remove the mean across satellites at each pair because
the carrier solve freely estimates one receiver clock change.

Compare the required signed correction to the archived final-minus-
broadcast satellite clock change on the common supported set. G17 has
no final clock samples and stays in the geometric calculation only.
Save the two signed vectors and report their RMS, difference and cosine.
Use the original post-fit range scatter for scale context only. Do not
fit a multiplier, change receiver positions or treat scatter after
position fitting as an independent range error bound.

Allow one setup and 240 pair operations, reserving 33 steps per pair
and one setup step. Use one worker and one thread, with a 180-second
cooperative limit and the separately qualified finite interruption
allowance. Use only sealed earlier study inputs from recording 187.
No new receiver solve, inertial fit or reserved flight read is allowed.

This tests a specific recorded satellite-clock correction against a
constructed displacement. It does not bound remaining satellite error,
neutral-atmosphere delay, antenna and tracking effects, or a combination
of those effects.
