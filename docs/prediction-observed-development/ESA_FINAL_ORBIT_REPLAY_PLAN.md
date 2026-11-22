# Isolate the effect of GPS satellite orbit corrections

Use the 1,041 half-second epochs already compared on ESA development flight
187. At each epoch keep the observed dual-frequency code, the exact
satellite set of the saved broadcast solution, its calculated transmit
times and broadcast clock corrections. Start from the sealed broadcast
position and receiver clock. Check that this state reproduces the
original range objective and is stationary within the original numerical
tolerance.

Replace only the satellite positions by interpolation in the hash-verified
IGS final orbit product. Use eight consecutive 15-minute GPS-time knots
around each transmit time, with a degree-seven interpolation. Apply the
same range solver linearization, Sagnac correction, troposphere model,
equal weights and elevation screen. A changed satellite set, invalid
solution or failure to settle within the fixed allowance remains a
failure in the epoch count. The finite run allows one baseline range check
and up to four replacement range evaluations per epoch, with one worker and
one numerical thread. Each task covers a predeclared disjoint block of at
most 120 consecutive epochs.

Verify the interpolation against a known polynomial, exact knot
evaluation and a missing interior knot before running. Report the signed
position differences, residual errors, convergence and the satellite orbit
displacements. This comparison tests a specific shared input of the three
receivers. It leaves the accurate time-dependent satellite clock correction,
other shared receiver error and absolute accuracy open. It reads only
recording 187, makes no inertial fits or forecast propagations and leaves
scientific confirmation closed.
