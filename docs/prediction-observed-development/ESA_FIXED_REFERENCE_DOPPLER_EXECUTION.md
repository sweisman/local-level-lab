# Reykjavík Doppler execution check

The first [Doppler study](ESA_FIXED_REFERENCE_DOPPLER_PLAN.md) closed
before computing any velocities. Its initial operation reservation
provided a step count without the required operation count. The
original start and error are retained in `data/esa-fixed-reference-doppler-v1`.

The corrected study applies the same observations, comparison and
velocity solver. It allows 3,662 velocity solves and one setup operation.
The charge is 3,663 bounded operations and 36,621 steps. The test
exercises the adapter's complete reservation sequence on a known
trajectory before the corrected study can run. One worker uses one
thread, with a 180-second cooperative limit and the existing finite
interruption recovery policy.
