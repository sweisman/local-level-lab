# Rebuild ESA velocity from the recorded Doppler shifts

Use the same sealed aircraft excerpt, broadcast navigation and all 1,041
half-second epochs. Estimate GPS-only and GLONASS-only velocities separately.
Each uses its sealed L1 code position at that epoch to compute the satellite
directions. Recover motion from the recorded D1C frequencies and broadcast
satellite velocities. Do not differentiate the receiver position series.
Use the GLONASS frequency slot to convert hertz to range rate.

Include the change in Earth-fixed geometry during signal travel and solve
for a separate receiver clock drift for each constellation. Use equal
weights, a fixed 5° elevation mask, at least five ranges and full rank.
Apply no residual-based exclusions or velocity smoothing. Atmospheric
delay rates and unmodeled receiver channel effects remain in the error.
Verify sign, clock drift and recovered direction against independently
generated range rates before running on the aircraft data.

Use one numerical thread and at most 2,082 linear solves. Seal the velocity
paths before reading the reported receiver velocities. The subsequent
comparison uses the previously fixed 520 time matches and reports the
earlier 400 and later 120 separately. The seven reserved flights stay
closed. The estimates share the aircraft antenna and, within each
constellation, the Doppler source receiver. This is a motion check on one
development flight. It does not establish absolute position accuracy.

[RINEX Doppler measurement format](https://files.igs.org/pub/data/format/rinex304.pdf)
· [GLONASS position result](ESA_GLONASS_COMPARISON_RESULT.md)
