# Replay the carrier paths with two observed atmospheres

Use the frozen 520-report ESA 187 interval. Replay each of the previously
qualified GPS and GLONASS carrier paths with both saved NOAA balloon
profiles. Reuse the first receiver position, satellites, orbit data, clock
correction, initial and updated endpoint position solves, and angle mask.
Check that each step uses exactly the satellites recorded in its sealed
standard-atmosphere path. Apply each station's regional column everywhere
in the replay without adjusting reported height. Keep the standard paths
as the reference without rerunning them.

For each of four tasks, allow 1,038 half-second pairs at no more than two
eight-iteration solves per pair. Use one worker and one numerical thread
with a 180-second cooperative wall ceiling. Record failed tasks and any
partial path. Neither inertial fitting nor protected-group access is needed.

For the 120 later reports, compare horizontal and vertical RMS differences
against the corresponding sealed path. Use the same frozen position
projection and shape-score direction to evaluate any ranking change.
Zero marks a shape-score tie. Report changes from both the replay's own
standard-atmosphere path and the processed export. These comparisons test
two regional atmospheric models. They do not constrain all aircraft-local
weather, antenna effects or position errors shared by the satellite paths.
