# Work out what one-second position anchors could add

Compare the four verified permanent Nuuk times with an ideal complete
integer-second grid over the same sealed 120-second score window. Keep
both endpoint positions fixed as in the previous motion test. Use the
archived time origin and all original signed score weights. The ideal grid
describes a possible measurement schedule. It gives no coverage or accuracy
estimate for the [Nuuk Museum file](ESA_GROUND_REFERENCE_AVAILABILITY.md).

On each interval between anchors, split a coordinate error into the linear
interpolation of its endpoint errors and a curve that vanishes at both
ends. Accumulate signed interpolation weights before taking their absolute
sum. Independently integrate the squared fixed-endpoint Green-function
kernel in exact arithmetic for the remaining score change. Relax continuity
of velocity between intervals to give a conservative bound. Verify that the
30-second bound on the minimum RMS acceleration does not exceed the already
solved minimum. [Exact four-anchor result](ESA_NUUK_BETWEEN_SAMPLES_RESULT.md)

Report the position error bound that would spend the entire score gap,
the lower bound on RMS acceleration needed with perfect anchors, and the
joint trade-off. Use the maximum absolute component at each anchor for
position and the vector RMS acceleration across the full window. A ground
receiver measures its own ranges. Applying this calculation requires
independent bounds on the resulting aircraft position errors and between-
sample acceleration errors.

Use one task with one operation for each schedule, one worker with one
thread and a 90-second cooperative cap. Use the qualified finite technical
recovery policy. Read sealed score evidence only. No receiver fit, new
ground observation or reserved flight enters the calculation.
