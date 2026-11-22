# Raw iMAR angular-rate baseline during the speed-selected ground interval

Use the exact 7,815-report interval selected by the receiver-only
[ground control](GROUND_RECEIVER_CONTROL_RESULT.md), intersected with the
IMU's published first/last timestamps. The IMU starts about 20 minutes after
the receiver interval begins, so the missing portion cannot be analyzed as
IMU data. This overlap is fixed before looking at any gyro value; require at
least ten minutes. Verify the complete original ESA iMAR file
`187_rqh01.txt` against its published SHA-256 and parse its documented
engineering-unit records with the existing strict streaming reader. Read
samples whose GPS time falls inside that timestamp overlap. Reject a timestamp
gap above 1.5 nominal 300-Hz periods; do not repair or interpolate.

Report the unadjusted mean angular-rate vector on the file's X/Y/Z axes in
degrees per hour, its magnitude, one-minute vector means, first/second-half
means, sample count, acceleration magnitude and temperature context. Do not
rotate into north/east/down, subtract a predicted Earth rate, fit a physical
model, or select a favorable subinterval after seeing the rates. Save source,
parser, selection, plan and code hashes. Use one numerical thread, no fit
starts and no protected groups.

This is an instrument-output baseline, not a measurement of Earth's rotation.
Unknown sensor bias, scale, processing, aircraft mounting and tiny ground
motions can affect it. A nonzero mean cannot identify the field's cause, and
a near-zero mean would not by itself establish that the raw sensor saw no
background rotation. This control helps determine what a later calibrated
field analysis must explain.
