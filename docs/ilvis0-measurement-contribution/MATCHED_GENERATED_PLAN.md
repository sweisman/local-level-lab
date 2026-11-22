# Matched field and offset qualification

The study tests the counted training and continuous forecast path before a
NASA pilot. Use four 24-second analytic flight histories, one for each
geometry and field combination. Use northern and southern latitudes, with
both straight and turning routes. Generate IMU packets at 200 Hz and
receiver reports at 1 Hz. The first 14 reports are training observations,
and the final nine are withheld. Generate the field and Coriolis terms
independently of the integrator. Add a fixed, small sensor-axis gyro offset
inside the tightest declared box.

For each trajectory and removal case, fit every candidate to identical
measurements across the ±1, ±3, ±10 and ±20°/hour per-axis boxes. Regenerate
the truth only after the continuous forecast is sealed for scoring.
Preserve all normalized calibration coordinates, convergence outcomes,
absolute physical position errors and charges. Keep the forecast horizon,
optimizer and common receiver weights fixed across candidates.

The matrix has 128 fit identities, one start each, with at most 80 fitting
calls and one forecast call per identity. Four workers may use one thread
each. There is a finite two-hour wall allowance and no numerical retry.
Any recovery must use the qualified task-level protocol and reuse sealed
outcomes. This study uses generated inputs and starts no observed fits.

The software checks require all identities to return without technical
failure and the complete fitted prefix to agree with the continuation
within the existing (10^{-8}) meter implementation scale. A truth-matched
fit must pass its numerical stopping checks and have withheld horizontal
and height RMS at or below 0.25 m before supporting the matched workflow.
Alternative-model failures are retained as unresolved comparisons.
Any cost separation or sensitivity to the cap is descriptive. This
qualification does not establish a calibrated decision threshold, raw
aircraft sensor error or the adequacy of a gyro-free aircraft motion model.
