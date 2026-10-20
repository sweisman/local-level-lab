# Native factorization to qualify

The component implementation `lll.ilvis0_shared_reference_terms` defines the
shared vectors, conservative radii, source/expansion binding and mandatory
27-plus-6 column interface. Its local tests cover nonzero rotation/lever
centers, actual nonzero levers, product identities and inconsistent bindings.
**It does not yet supply a factored native remainder.**

## Preserve initial velocity algebraically

Let `v = v_initial + delta_v`. In the midpoint update, with skew argument `a`
and `B = (I+[a]x)^-1`, compute the velocity increment as

`increment = -2 B (a x v) + B rhs`.

Accumulate `delta_v` directly and reconstruct the complete velocity from the
initial bound plus that increment. The estimate used for the native midpoint
must remain the same estimate as in the original solver; changing it to an
average based on the final corrected velocity would change the numerical model.

For each coordinate let `m_initial` be a fixed initial metric coefficient and
`m(position)` the bounded current coefficient. Split rates exactly:

`rate = m_initial*v_initial + m(position)*delta_v`
`       + (m(position)-m_initial)*v_initial`.

The residual integral contains only the last two terms. The reference product
uses the correlated clock, rather than separately multiplying the uncertain
initial velocity by every uncertain packet cutoff.

Write the clock as `S = S_center + slope*delta_tau + e_clock`. The initial
velocity is linear in its three calibration coordinates. Its product has a
shared term `slope*m_initial*gamma_v`; after separating it, a conservative
remaining product allowance is

`(|reference_rate_center| + reference_rate_change) * clock_remainder`.

Any nonzero reference-rate remainder also needs its complete product terms;
the shortcut above assumes the declared reference rate is linear. Intermediate
body/geographic states must retain the **full** reference-product bound. Only
the final observation may factor out the common term. This preserves its
indirect effects on metric, field and transport calculations.

## Preserve the initial lever remainder algebraically

Let `initial_action = R0 L`. Its full change bound remains available, but its
Taylor remainder is the shared vector `gamma_L`. Map a value with the same
center/change and zero **unshared** remainder through the final metric. The
metric-times-action cross term must still use the full action change, including
the shared uncertainty. The removed term is `metric_center * gamma_L`.

The remaining action is `(Rt-R0)L`. An operator-norm bound for `Rt-R0` follows
from telescoping the left navigation and right body rotation products:

`B_rotation = min(2, sum(body_angle_bounds) + navigation_rate_bound*T)`.

A conservative speed bound is the initial speed bound plus all corrected
delta-V norm bounds and `gravity_max*T`, because the Cayley factor is a rotation
and its inverse-skew factor is a contraction. It bounds height/latitude
variation, positive geographic metric minima and transport rate. Unsupported
polar/metric domains must abstain. Restore the actual model/removal background
bound; no physical term disappears.

For a general nonzero lever center, the derivative of `Rt-R0` applied to the
parameter displacement is bounded by the sum of the current/initial attitude
change and remainder bounds. Consequently a safe, possibly loose action
remainder is

`B_rotation*(lever_max + lever_center_norm + lever_change)`
`+ derivative_delta_rotation_bound*lever_center_norm`.

Its actual center is `(Rt_center-R0_center)*L_center`, and its full change can
be bounded by `B_rotation*lever_max + norm(actual_center)`. Passing those bounds
through the geographic metric retains the metric's derivative and cross terms.
At a zero lever expansion center this simplifies substantially while still
covering every nonzero actual lever in the original region.

## Joint output contract

The complete mean and 27 native tangent columns remain those of the original
physical predictor. The six added columns multiply normalized bounded shared
vectors. Coefficients and all epochs must have the same source/domain/expansion
binding. A native consumer cannot use a shortened unshared remainder without
the associated columns. Distinct recordings cannot share a block merely because
their configuration bytes agree.

Qualification must subtract the **actual known-control shared vectors** from
each native Taylor residual before checking the unshared remainder. Include
both signs, nonzero centers, timing endpoints and all candidates/processing
cases. Reconcile total centers/Jacobians against the unchanged engine and
preserve full inputs, inequalities and certificates. A pass still does not
establish whole-program numerical enclosure or observational coverage.

[Design and gates](PLAN.md) ·
[Saved diagnostic evidence](../ilvis0-regrouped-constraint-audit/INTERPRETATION.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
