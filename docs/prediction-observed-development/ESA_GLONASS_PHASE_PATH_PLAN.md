# Compare carrier-phase motion from two satellite constellations

Use the 520 assigned reports and the same first earlier receiver
position that anchored the GPS carrier-phase replay. Use only
GLONASS carrier phase, matching code for transmit time, and broadcast
GLONASS orbit and clock data for this new path. Apply the preflight's
receiver clock step only at the original exceptional pair.

At each half-second step, use one healthy broadcast ephemeris per
satellite at both endpoints, with its frequency channel matching
the observation header. Require both transmit times within 900
seconds of that ephemeris. Select the nearest eligible common record
without using position or carrier residuals. Reuse the displacement
solver, elevation and condition checks, common receiver clock
adjustment and two atmosphere evaluations from the GPS replay.
Use the established broadcast coordinate convention for both paths.

Allow 1,038 paired steps, with at most two eight-iteration solves per
step on one thread. Stop and preserve the failure if one step cannot
be solved. Use no later position updates. The separate report compares
GLONASS against the processed export and the sealed GPS carrier path,
then measures how the GLONASS path changes the fixed shape score.
The two constellations share an antenna and anchor. The comparison
cannot identify errors shared by both systems. No new inertial fit
or protected flight read is allowed.
