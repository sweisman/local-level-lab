# Test a shape contrast that suppresses the calibration effects of both forecasts

The original contrast uses the difference between the two nominal
zero-field forecasts. Its calibration allowance exceeds that
difference. Look for a contrast that retains variation from the
nominal forecasts while suppressing the trajectory changes available to
both models under calibration.

Use the original 400 earlier times, 120 later times, two sealed
forecasts and the same fixed forecast covariance. Build all 51
calibration columns for each candidate from the archived trajectory
approximation. Keep the nine smooth displacement terms from the
original comparison. In whitened coordinates, propose three contrasts
after removing that smooth span and suppressing zero, half or all
numerically resolved singular directions of the combined calibration
matrix. Normalize nonzero proposals to unit Euclidean length before
converting them back to position coefficients. The numerical choices
only propose directions.

Treat the converted position coefficients as exact rational numbers.
Adjust three later coefficients per axis at the first, middle and last
epochs so they annihilate constants, linear trends and quadratic
trends exactly. Verify all nine zero sums. Both forecasts retain
all their calibration columns in the bound, including any direction
the numerical construction could not resolve. Compute the signed
nominal contrast and the worst movement over the full archived
coefficient boxes using rational arithmetic, without tighter earlier
loss assumptions. For each positive remaining margin, report the
largest uniform per-coordinate nonlinear position error the contrast
can absorb across the two forecasts.

The result applies to the archived local trajectory approximation and
coefficient boxes. It does not provide the nonlinear integration
bound or qualify the aircraft forecast error model. No new observed
positions, new trajectory fits or reserved flights are used.

Use one task on one thread, with seven bound calls, 13 steps and a
180-second cooperative allowance. Charge the direction construction
once, then charge the adjoint and exact coefficient checks for each of
the three proposals. A zero numerical contrast yields an explicit
unavailable outcome. Freeze the original sealed ranges and source
files. Retain at most one charged recovery attempt with the same
180-second recovery allowance.
