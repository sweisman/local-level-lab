# Test the change over time in GPS satellite clock corrections

Use the same 1,041 half-second epochs from development flight 187. Both arms
exclude G17 because its final clock is unavailable. The broadcast orbits,
transmit-time calculation, observed code, range model and remaining satellite
sets match between arms. At every epoch start the restricted broadcast arm
from the sealed full-set position and check the original full-set objective.
Start the second arm at the restricted broadcast solution.

Interpolate the final clocks linearly at the original signal transmit times
without extrapolation. Subtract each satellite's broadcast clock correction.
Express these differences relative to GPS satellite G01, present throughout.
For each satellite subtract its first available relative difference before
adding the remainder to its broadcast clock. This isolates temporal changes
and discards unverified constant offsets. It leaves the original signal
transmit times fixed and does not substitute an absolute final clock model.

Freeze the source and input hashes, including the per-satellite anchors.
Check four range evaluations per arm plus one saved-objective check on the
baseline. Charge each start and its full evaluation allowance before use.
Use nine disjoint consecutive blocks and one numerical thread. Preserve
every failed or missing epoch. The paired forecast rescore uses the same
120 archived GPS match indices and the two complete forecast settings.
Separately report the effect of excluding G17 and the effect of the temporal
clock change on the resulting common set.

Check exact clock knots, interpolation, missing samples and cancellation of
constant offsets and shared epoch shifts. Check the runtime contract on one
opened epoch. This is a processing sensitivity test. No independent flight,
inertial fit or forecast propagation is part of the test.
