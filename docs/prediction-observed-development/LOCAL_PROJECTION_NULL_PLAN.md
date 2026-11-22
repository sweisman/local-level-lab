# Local fitted-error projection control

Question: Can fitting the 26 free calibration directions alone produce the
height-error correlation found in the opened ESA development recording?

Read only the two sealed 600-report ESA training fits and their sealed
innovation report. Verify archived hashes, residual convention and length,
full tangent rank, no active bounds, and near-orthogonality of the fitted
residual to the tangent. Use each fit's saved **whitened** Jacobian to project
2,048 seeded independent standard-normal error histories onto the tangent's
orthogonal complement. Report the distribution of lag-1 and lag-20 height
correlation, the observed values and the number of simulated histories at
least as extreme. Use the same random histories for both laws.

Finite allowance: exactly 2,048 histories per law, no optimizer calls, no
original IMU/GPS reads, no later receiver reports, no reserved ESA groups.
One numerical thread. Save source/input hashes, seed, projection rank and
all summary statistics. This is a **local linearized conditional control**:
the tangent was estimated from the same observed fit and the supplied
covariance is assumed correct. It does not test nonlinear refitting, model
error, or the aircraft error law itself. The scientific decision stays
abstain, regardless of the simulated result.
