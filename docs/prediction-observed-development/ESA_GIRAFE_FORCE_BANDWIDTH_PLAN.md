# Test the effect of averaging the two force streams differently

Use the same eight opened ESA windows, the same two receiver kernels
and the logged UTC alignment from the sealed GIRAFE overlap study.
Reproduce its original averages before comparing alternative summaries.

Transport the iMAR vectors to a common starting orientation using the
logged gyro, and apply the same working correction to move them to
GIRAFE's location. Preserve the 10 Hz GIRAFE sample cells. On each
receiver support compute three iMAR quantities in order:

1. Average the magnitudes of the original iMAR samples.
2. Average the iMAR vectors within each GIRAFE time cell, take the
   resulting magnitudes, and average over the support.
3. Average the iMAR vectors over the entire support, then take the
   magnitude.

Preserve the integral of the original receiver kernel across the cell
boundaries. The second calculation therefore removes within-cell
variation without changing how much weight each cell has. With matched
weights, the three quantities must decrease in this order. Also compare
the two available GIRAFE summaries. Its vector means use the recorded
platform axes, whose changes relative to the aircraft are unmeasured.

Report how much of the signed sensor difference changes under each
calculation. This changes the averaging operation on existing data.
It does not reproduce the GIRAFE instrument's internal filter or
isolate platform movement, physical motion or either sensor's error.

Freeze eight tasks with one packet pass per window, at most 121,000
intervals each, one numerical thread and a 150-second limit. Use the
original overlap study's sealed GIRAFE and iMAR data. No additional
recording, calibration fit, model decision or reserved-flight access.
