# Separate the two carrier bands in the Reykjavík discrepancy

The [all-satellite phase comparison](ESA_FIXED_REFERENCE_PHASE_RESULT.md)
shows a 0.85 m vertical RMS disagreement with the aircraft's GPS path.
It keeps the ten continuous dual-frequency satellites under one
geometry. This check measures how much of the discrepancy comes from
the difference between the two recorded carrier bands.

Use the archived 61 times, the same ten satellites, the original first
GPS position and unchanged ephemerides. At each later time, take the
change in the aircraft-minus-station carrier measurement on each band.
Subtract those two changes before solving. Geometric range cancels in
this difference. Use the same three position columns and common clock
column as before. Subtract the resulting band contribution from the
known combined solution to recover the separate single-band solutions.
Compare all three paths with the same aircraft GPS path. Preserve the
per-satellite band changes and the two receivers' individual changes.

Neither single-band solution removes the first-order ionosphere term.
This is an explanation of a measurement difference, with no selection
of a more favourable path. Keep every original satellite and time.
Freeze one task with one input check, 60 ten-satellite geometry checks
and 60 four-parameter linear solves, for 61 charge groups and 661
work steps. Use one numerical thread, a
180-second cooperative limit and one independently charged recovery
attempt. No new source reads or aircraft inertial fits are required.
