# Global bounds for calibration and rotating-force increments

This study addresses two actual nonlinear components of the native prediction
map: reciprocal bias/gain correction and finite rotation of measured velocity
increments. It is a prerequisite for a native global error bound, not that bound
in its entirety. No observed data or fitted Earth-model outcomes are used.

## Exact mathematical bounds

For one corrected component, let `q = (raw - bias*dt)/(1+gain)`. At a supplied
center write `A = raw - bias0*dt` and `d = 1+gain0`. If the complete box has
`1+gain >= dmin > 0`, with maximum center displacements `B` and `G`, the first-order
remainder is bounded by

`abs(A)*G²/(d²*dmin) + dt*B*G/(d*dmin)`.

Compute corrected-value extrema at the bias/gain rectangle's corners and combine
all three axes conservatively in Euclidean norm. These are bounds for the entire
declared box, not maxima inferred from test probes. Preserve signed increments.

For the skew-matrix exponential, the derivative norm is at most one and the
second-order Taylor coefficient at most one half. For its velocity integral
`J = integral_0^1 Exp(u*theta) du`, the corresponding constants are one half and
one sixth; for the position integral
`K = integral_0^1 (1-u)*Exp(u*theta) du`, they are one sixth and one twenty-fourth.
The value norms are at most one, one and one half for rotation, J and K.
These follow from differentiating the exponential integral, with orthogonal
factors having norm one. They hold beyond a small-angle neighborhood.

For `M(theta)*dv`, propagate both actual parameter changes and the nonlinear
remainders of corrected `theta` and `dv`. Include their product term. A bound
that omits that term is not a bound for joint calibration uncertainty.

Propagate rotation, velocity and position change/remainder radii through a
fixed-duration body-frame preintegration. Shared calibration across packets is
allowed: triangle inequalities do not assume independent packet errors. Norm
bounds may be conservative and are not statistical confidence intervals.

## Qualification

Thirty fixed software identities:

- Twelve three-axis calibration boxes: angle/velocity increments, centers at
  lower/zero/upper bounds, and narrow/broad calibration. Evaluate all 64 corners
  of each six-dimensional box.
- Twelve rotating-force cases: rotation/J/K, small/large center rotation, and
  narrow/broad perturbations. Sixty-four fixed joint angle/velocity probes each.
- Six fixed-time histories: 1, 7 and 31 packets under narrow/broad calibration.
  Sixty-four shared twelve-parameter probes each.

Use a separate nine-dimensional block-matrix exponential and its Frechet
derivative as the value/tangent reference for rotation/J/K. History references
propagate those matrices and directional derivatives independently. Compare
with the repository's existing within-packet/preintegration implementation;
never generate a bound from a largest measured discrepancy.

Require each actual change and Taylor remainder to lie within the analytic
radius, allowing `1e-12*(1 + norm(reference) + norm(linear_term) + radius)` for
the numerical comparison. This is a qualification tolerance, not a proof of a
whole-record floating-point rounding envelope. Preserve failures without retries.

Limits: 30 identities, 1,920 probes, at most 13,000 software packet/reference
evaluations, 300 cooperative seconds, one worker/four threads, no original reads,
optimizer starts, native-engine evaluations or retries. Charge before execution
and preserve sources, inputs, environment, generated parameters and all results.

The task list reserves 12,726 reference/value evaluations before execution.
Center derivatives are reused across probes. Each identity's complete allowance
is charged up front; interruption does not refund its unused portion.

## Remaining native terms

These bounds do not yet cover candidate-dependent transport, gravity, geographic
coordinate conversion, lever arms, rotation-removal processing or uncertain
receiver timing across packet boundaries. Nor do they establish a machine-
roundoff bound for long integrations. The prediction interface must still return
unsupported when any required global term is missing. No archive prediction
fit or empirical coverage claim follows from passing these component controls.

[Native interface](../ilvis0-bounded-prediction-controls/NATIVE_INTERFACE.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
