# Check the separate GLONASS carrier signals

Use the unchanged AIR1 RINEX excerpt on recording 187 and all 1,040
adjacent pairs. Use the C/A carrier and matching Doppler on each
band. Require the same slot at both endpoints and use its frequency
channel from the RINEX header. Reject missing fields and nonzero
loss-of-lock flags. Require Doppler agreement within 0.35 cycles on
both bands and agreement of the two range changes within 0.075 m.

At the one independently diagnosed receiver clock break, apply the
same one-millisecond change using each GLONASS channel's frequencies.
Check Doppler using the corrected elapsed time. Record that case
separately and leave the measurements and original GPS result intact.
No new clock estimate from trajectory fits is permitted.

Report all rejected satellite pairs and count pairs with at least five
satellites. This is a support check for a later relative-position solve.
It allows one continuity pass and zero position solves, inertial fits
or protected flight reads. [RINEX 3.04 GLONASS frequencies and observation fields](https://files.igs.org/pub/data/format/rinex304.pdf)
