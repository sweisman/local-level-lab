# Change the GPS motion while keeping the same force calculation

Use the 991 complete [carrier-phase windows](GPS_CARRIER_PHASE_RESULT.md).
Build a path in Earth-centred coordinates by adding the saved phase
displacements within each window. Anchor each path at the original onboard
centre fix. This keeps the position and altitude reference fixed at that
instant and tests what changes when the surrounding motion comes from carrier
phase. Every window must retain exactly its original receiver times.

Use the same quadratic position weights, four shape and background-field
candidates, two packet clocks and saved whole-packet intervals as the
[original force calculation](MATCHED_FORCE_AVERAGE_RESULT.md). Keep the
original ±0.15-second timing allowance and eight interval subdivisions. Check
whether the same-field shape ordering survives, and how often the difference
in a candidate's centre force exceeds the corresponding onboard shape gap.

Apply the previously recorded training gains to both onboard and phase paths
without fitting new gains. Compare the accelerometer lower-bound violations
separately in training and later windows. The motion estimates share satellite
and propagation errors. This comparison checks the effect of changing the
motion input and supplies no absolute calibration or decision threshold.

Use one numerical thread, 7,928 force envelopes and at most 63,424 interval
evaluations, with zero position solves, gyro observations and inertial fits.
Freeze the program, saved inputs and environment before calculating. Verify the
identical output through a saved-input replay.
