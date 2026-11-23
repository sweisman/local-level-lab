# Replay antenna phase with a fixed upright receiver

Add ideal GPS antenna rotation corrections to the same two-minute
development score used for the earlier antenna calibration check. Use
the aircraft path, satellite positions, satellite attitudes and Nuuk
receiver coordinates already sealed by that check. Treat both receiver
antennas as pointing up in their local frame. The measured aircraft
attitude and installed antenna response remain open.

Calculate the signed fractional phase with the crossed-dipole model.
Difference phase at each pair of endpoints before removing common phase
across satellites. Require a continuous short phase change on each
retained arc and preserve the original satellite sets, weights and
reference ranges. Report the change to the full aircraft score and the
covered aircraft-minus-ground score, each relative to the original
gap. Also report the smallest satellite elevation along the aircraft
path. This sets a geometry limit on the ideal tilt bound for the
sampled rays. [Phase equations](https://ntrs.nasa.gov/citations/19920060722)

Use one task and one thread. Allow one setup, 240 half-second aircraft
pairs, 120 one-second ground pairs and at most 132 charged checks per
pair. The replay uses no additional recordings, model fits or reserved
flight data. Preserve the original range scores and the earlier phase
centre correction. Apply the standard charged interruption recovery
rules if needed.
