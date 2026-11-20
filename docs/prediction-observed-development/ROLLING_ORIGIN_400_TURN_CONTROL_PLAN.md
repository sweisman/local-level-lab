# Receiver-only constant-turn forecast

The existing GPS-only controls hold the last course fixed. This later-designed
development control asks whether allowing one course turn rate narrows their
gap to the sealed IMU forecast. Its rule is fixed before scoring it; the prior
fixed-course misses were already known, so this is not independent validation.

Use the same sealed ESA recording-187 cut: 400 earlier receiver reports and
120 later reports. Read only the last 60 earlier GNSS-reported north/east
velocities and their timestamps. Unwrap course, fit one least-squares course
rate against time, and keep the final reported horizontal speed and upward
velocity fixed. Starting at the last earlier GNSS position, advance on a
spherical path in one-second or shorter steps, using the fitted course at
each step's midpoint. Forecast every sealed later timestamp with the same
rule; read later positions only for scoring. Do not use IMU, fused navigation,
or later GNSS values to fit or update the path.

Report the fitted turn rate and scored north/east/up errors alongside the
earlier fixed-course GPS-only controls and the sealed IMU forecast. The GNSS
position and velocity share one PPP solution. This single development window
cannot isolate a gyro contribution, calibrate uncertainty, or establish an
Earth-model decision. Keep all protected ESA groups closed.
