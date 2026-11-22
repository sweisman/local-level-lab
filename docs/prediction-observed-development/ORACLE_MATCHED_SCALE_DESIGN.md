# Matched error scales for the long generated forecasts

This finite software control asks whether the two saved 900-second noisy
forecasts have error magnitudes compatible with their **declared generating
laws**. It does not estimate a law from the ESA recording or decide an Earth
model.

The inputs are the sealed clean and noisy known-calibration controls. Before
numerical work, the generated 300 Hz angle, velocity and time increments must
match the clean control's recorded array hashes exactly. The spherical
rotating model, 55° latitude, fast climbing path, 900 receiver epochs at
0.5-second offset and 600/300 split are fixed. The two tasks use the existing
increment-error and point-rate-error definitions, respectively. Each task
has 270,900 native derivative calls and packet visits, no optimizer starts,
no random draws and no original or protected recording reads. Two one-thread
workers may run for at most two hours; their work is charged before execution.
Technical interruption recovery is limited to two attempts per task and
preserves completed numerical failures.

The operator receives the same known initial state and calibration as the
saved oracle forecast. Future receiver noise is disabled because the target
is error against physical future truth, not a future noisy receiver report.
Report the expected horizontal and vertical RMS scales from the future
covariance and the saved realized RMS values. No single-draw ratio is a
coverage probability. Any mismatch in trajectory, source, input or
environment stops the calculation. Keep the seven reserved ESA confirmation
groups closed.
