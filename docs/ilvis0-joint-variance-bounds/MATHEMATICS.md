# Marginal variance over a clock interval

For the stated linear inertial-noise model, let \(Q_a\) and \(Q_g\) be the
acceleration and gyro white-noise spectral matrices, \(G\) the constant
orientation-to-acceleration coupling, and \(t_0\) the fixed noise origin.
At elapsed time \(s=t-t_0\geq0\), position variance on axis \(i\) is

\[
V_{I,i}(s)=\frac{s^3}{3}(Q_a)_{ii}
          +\frac{s^5}{20}(GQ_gG^T)_{ii}.
\]

All coefficients are nonnegative when the spectral matrices are positive
semidefinite. Therefore the upper time endpoint gives the largest inertial
variance over the declared interval.

The receiver contribution is

\[
V_{R,i}(t)=W_{ii}+O_{ii}+\sum_j S_{j,ii}
 +D_{ii}\left(\frac{t-t_D}{T_D}\right)^2.
\]

Here \(W\) is white receiver error, \(O\) a random constant offset, \(S_j\)
stationary correlated components, and \(D\) the random drift coefficient.
The drift term is bounded using whichever interval endpoint is farther from
its own fixed origin \(t_D\); that need not be the later endpoint.

Sum these two bounds under the supplied independent-driving-error model.
The resulting observation errors remain correlated across times and axes.
The [simultaneous allowance](../ilvis0-gaussian-allowances/MATHEMATICS.md)
does not require those observations to be independent.

The implementation treats the finite input binary64 coefficients as exact
rationals. It verifies covariance symmetry and all seven principal minors of
each three-by-three covariance, evaluates the formulas exactly, and returns
outward binary64 endpoints. No eigenvalue clipping, interpolation, origin reset
or silent hardware specification is introduced.

The proof applies to this stated constant-coupling linear law. It does not prove
that the law describes a flight, that nonlinear effects are negligible, or that
a separately estimated common noise scale has the required coverage.

[Software checks and limits](README.md) · [Error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md)
