# Swap the velocity source in the fixed direction forecasts

Reuse the 36 locally stationary calibration fits on the opened ESA
development flight. Reproduce the starting rotation on the same first
eight directions with the training receiver source. Keep the calibration
and rotation fixed. Score the last eight directions against each of the
three velocity sources using that same rotation. The only change within a
row is the source used to compute the later required directions.

Preserve both averaging widths and all three matched field settings.
Verify every diagonal score against the saved exact correction. Report
all 54 globe-versus-disc comparisons, including each off-diagonal pairing.
Measure the change in the paired angular RMS gap when changing the scoring
source at fixed training and when changing the training source at fixed
scoring. Test whether the 11-report retained-field GLONASS reversal follows
training or evaluation. Retain the complete matrices and do not select a
receiver source based on the later errors.

Freeze 36 replays of 119,865 packets, one numerical thread and a 120-second
wall allowance. No instrument calibration is re-estimated. The source swap
is a sensitivity check on earlier selected data from one flight. The
receiver products share a position reference and antenna. Their spread
does not establish a bound on common errors or independent accuracy.
Read no reserved groups or 120 position forecasts from the original cut.
