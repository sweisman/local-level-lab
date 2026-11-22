# Propagate reported receiver velocity uncertainty into the force comparison

Use the eight previously sealed 400-report windows, all three matched
receiver products, both averaging widths and both gravity assumptions.
Compare the same globe and disc models with a matching background
field. Reproduce the saved force means before propagating uncertainty.

Differentiate the existing force average with respect to the nine
velocity-polynomial coefficients using centered differences, with
two fixed step sizes. Use the fit's linear weights to pass the
derivative back to the individual north/east/up velocity reports.
Hold position fixed. Use the same earlier-mean removal as in the
force-only comparison and propagate it jointly across supports.
Reject a support derivative if the two step sizes differ by more than
5 × 10⁻⁹ m/s² per m/s at any velocity component.

Use each receiver's full printed velocity covariance. Test independent
epochs, exponential correlation with 5, 30 and 120 second time constants,
and a fully shared standardized error. Also compute the largest
linearized standard deviation of each scalar if cross-time dependence
is arbitrary. In the shared-error cases, the whitened velocity axes
are coupled across time through the Cholesky factors of the printed
covariances. Use the same realization for both shapes when propagating
their force difference. These are declared sensitivity scenarios.
The true covariance across time and between position and velocity is
unmeasured. The printed covariance has unverified coverage.

Report the absolute force prediction scale and the paired prediction
scale alongside the original shape difference. The uncertainty in the
paired difference can be much smaller because the receiver input is
shared. The comparison supplies no calibrated significance or absolute
flight-error allowance.

Freeze eight tasks, one numerical thread and a 150-second limit.
Allow 96 support operations and 1,932,288 quadrature points per
window. Use exact frozen receiver inputs and saved force results.
No new receiver decode, recording, reserved flight or calibration fit.
