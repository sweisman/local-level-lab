# Global bounds for the native midpoint local step

This follows the completed calibration/rotation component study. It addresses
the actual local step used by the prediction engine, rather than substituting
constant-body-force preintegration. No archive originals or model fits are used.

## Mathematical propagation

Represent each input by its nominal value, maximum change over the complete
declared region and first-order Taylor remainder. Keep scalar/vector and
orthogonal/contraction matrix structure distinct. For products, retain the
product of input changes; independence is not assumed.

For `B(a)=(I+S(a))^-1`, skew symmetry gives operator norm at most one. The
resolvent identity bounds its change by `min(2, norm(delta_a))` and its
first-order remainder by `norm(delta_a)^2`. For `T(a)=2B(a)-I`, orthogonality
gives change bound `min(2, 2*norm(delta_a))` and remainder coefficient two.
Add input approximation errors through their derivative bounds. Exponential
rotations use the previously qualified global derivative bounds.

Propagate

`win = physical_background + transport - removal*standard_background`,
`a = (2*physical_background + transport)*dt/2`,
`middle = Exp(-win*dt/2)*attitude*Exp(theta/2)`,
`attitude_next = Exp(-win*dt)*attitude*Exp(theta)`, and
`velocity_next = T(a)*velocity + B(a)*(middle*dv + gravity*dt)`.

The standard background is `Omega*(cos(latitude),0,-sin(latitude))` for every
candidate. The physical background is that vector only for the specified-field
globe. Removal does not change the physical Coriolis argument. Bound latitude
dependence and the removal/vector product jointly. Preserve positive gravity,
removal in [0,1], fixed positive dt and supported latitude domains.

## Independent comparisons

Use SciPy matrix exponentials and linear solves for a separate value reference;
use complex-step directional derivatives of that reference. Separately compile
a thin wrapper around the existing static C local step. The wrapper includes
the unchanged kernel source and performs no full-record integration.

Thirty fixed cases: all three candidates, latitudes ±65°, fixed-zero/profiled
removal and narrow/broad parameter boxes (24 cases), plus zero-rate centers for
each candidate/removal pair (six cases). Each case uses 64 predeclared probes
in a shared 24-parameter input box. Keep all inputs, parameter vectors, nominal
values, derivatives, remainders and failures. Broad cases include a full yaw
range; tests are not restricted to a favorable local neighborhood.

Require observed changes and Taylor remainders within their analytic radii, and
C/reference agreement within `2e-12*(1 + norm(value) + norm(linear_term) + radius)`.
This numerical comparison tolerance is not a whole-record rounding certificate.
Each identity reserves all 65 C calls and 129 independent reference calls before
execution. No interrupted allowance is refunded or retried.

Limits: 30 identities, 1,920 probes, 1,950 software C local-step calls, 3,870
independent reference calls, 300 cooperative seconds, one worker/four threads,
zero original reads, archive-native sweeps, optimizer starts or retries. Freeze
source, compiler configuration, binary, inputs and numerical environment before
execution. Check the wall allowance between bounded operations; use no signals.

## What remains

The local step assumes global input bounds. Candidate geographic-rate/context
generation and predictor/corrector closure are next, followed by lever arms,
receiver timing across packets and long-record arithmetic. A component pass
does not supply missing bounds or observational covariance calibration. No
archive prediction fit follows automatically.

[Previous components](../ilvis0-increment-remainders/INTERPRETATION.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
