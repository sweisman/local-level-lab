# Compare the predicted shape difference with measured force disagreement

Use the eight sealed ESA 187 windows and both force averaging widths.
Keep the GIRAFE and raw iMAR magnitudes from their logged clock
alignment. Use the raw iMAR magnitude so the primary comparison uses
neither the logged iMAR gyroscope nor a fused orientation.

Compute the required acceleration magnitude from the saved receiver
positions and velocities for both shapes. Compare globe and disc
under zero background field and again with the specified field
applied to both. Use the existing matched force evaluator under
its fixed-gravity and height-dependent-gravity assumptions.

Use the `air1` epochs as the reference. For the two already verified PPP
exports on this flight, require all 400 times to match within 2 ms,
with no reuse or interpolation. Preserve unavailable comparisons if
coverage is incomplete. The receivers share an aircraft antenna.
Disagreement between receiver products is evidence about relative
error only. The predicted magnitudes refer to the antenna trajectory,
while the observed magnitudes refer to the two instrument locations.
Their motion differences remain part of the error in these gyro-free
scores.

Subtract each sensor/model pair's mean residual on the first eight
supports, then score only the last eight. Compare the remaining
globe–disc prediction difference with two baselines after removing
the same kind of earlier mean. The first is the difference between
GIRAFE and iMAR. The second is the change in each predicted force
between receiver products. Report score order and geometry margin
separately. The observed differences are diagnostic scales, with
shared errors and temporal dependence still unmeasured.

Freeze eight tasks, one numerical thread and a three-minute limit.
Each task is allowed at most 768 force averages or 52,224 quadrature
points. Use only receiver paths and saved magnitudes from the opened
flight. No inertial packet propagation, independent flight, calibration
other than the declared constant residual offset, or scientific
decision.
