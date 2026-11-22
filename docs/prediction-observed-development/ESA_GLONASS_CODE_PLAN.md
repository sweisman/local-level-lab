# Rebuild ESA positions using GLONASS only

Use the same sealed half-second AIR1 observation excerpt and daily RINEX
broadcast navigation file already used for GPS. Test the RINEX GLONASS
clock sign, epoch conversion, kilometre scaling and frequency-slot fields.
Check orbit propagation in both directions against a separate, high-accuracy
inertial-frame integration. Check a full pseudorange receiver solve against
a generated position with a known common clock offset.

Run two fixed code choices over all 1,041 epochs. Use C1C alone with the
existing broadcast GPS ionosphere correction as a working atmosphere
model. Use paired C1C/C2C with the GLONASS ionosphere-free combination
as the second choice. Use GLONASS broadcast clocks and satellite orbits in
both. Treat PZ-90.11 and the GPS comparison frame as coincident at the
precision of this code-only experiment. Use the fixed RINEX header seed,
the existing atmosphere and 5° elevation mask, and equal weights. No
satellite exclusions based on residuals. Report the effect of unresolved
receiver and satellite channel biases as a limitation.

Allow 2,082 position starts with at most 12 updates each. Require five
ranges and a full-rank four-parameter solve. Retain every abstention. Use
one numerical thread and freeze the source, environment and inputs before
running. Save both paths before comparing them with the receiver export
or forecast scores. No inertial data, new Earth-model fits, or reserved
ESA groups enter this study.

[RINEX 3.04 GLONASS record and clock conventions](https://files.igs.org/pub/data/format/rinex304.pdf)
· [Broadcast equation reference implementation](https://github.com/tomojitakasu/RTKLIB/blob/master/src/ephemeris.c)
· [GPS comparison](ESA_RINEX_CODE_COMPARISON_RESULT.md)
