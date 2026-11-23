# Can a nearby GPS correction carry forward in time?

Use ESA development flight 187. Fix the earlier block at GPS week seconds
388215–388550 and the later block at 388614–388734. The blocks are the same
ones used in the Qaqortoq transfer. They are separated by the receiver
clock step. Reuse the sealed earlier aircraft and Qaqortoq range differences
and the two sealed later ground comparisons. Decode the Nuuk Museum
station day and reproduce its earlier range differences with the same
satellite products used in both prior comparisons.

For each one-second interval keep satellites with continuous observations
from all three receivers. Require at least five, center each receiver's
ranges on that common set and preserve gaps. Recenter both sets of saved
later score weights on the intersection and check that they agree. Check
that the two saved aircraft vectors agree there as well.

Fit one multiplier per station using only the earlier residuals. Apply
each multiplier to the later measurements. Report the shared counts, the
later aircraft RMS before and after correction and the signed change to
the saved score, scaled by the original score gap. Use the existing Qaqortoq
transfer estimator so the two corrections are directly comparable.

Freeze one task with one thread, a 180-second cooperative cap, one setup
charge, at most 335 earlier station interval checks and 120 later interval
checks. Qualify common support and held-out behavior with deterministic
tests. Use the verified task recovery policy. This check measures transfer
on a single development flight. It cannot establish an error bound for
the aircraft antenna or qualify confirmation flights.
