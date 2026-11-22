# Check exact stationarity of saved joint calibration proposals

Use all 108 saved joint gyro and accelerometer proposals on the same
opened ESA flight. Keep the earlier eight force directions, three receiver
sources and three matched field conditions. Derive the gyro-rate tangent
through every ordered packet rotation to the last earlier support. Combine
it with the exact accelerometer correction and normalization derivatives.
Eliminate the same proper starting rotation before checking the derivative
of earlier squared chord loss.

Use the existing normalized calibration box and projected-gradient limit
of 10⁻¹⁰. Preserve the original approximation and replay dispositions and
separately report what the exact check would accept. Do not refit or revise
the saved model rankings. Report how many pairs still have an eligible
earlier stationary point for both shapes. The check tests local first-order
stationarity and does not certify a global optimum or physical adequacy.

Allow one derivative packet pass per saved proposal and at most 60,000
integrated intervals per pass, on one numerical thread within 120 seconds.
Validate the derivative against finite differences of noncommuting
synthetic rotations first. Read no reserved flight groups or original
forecast's later 120 position reports.
