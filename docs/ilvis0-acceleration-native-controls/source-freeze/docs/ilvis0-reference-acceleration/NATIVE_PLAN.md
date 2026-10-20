# Native reference-acceleration construction

The component qualification is complete. This plan specifies the next candidate;
it permits no observed fits. Add a separate module rather than editing completed
shared-reference sources. Keep all 27 physical bounds and the native midpoint
equations. A new finite native qualification must be frozen before execution.

## Preserve relative attitude, including its derivative

A coarse bound on `(R_mid-R_initial)*f_reference` is insufficient: subtracting
two independently bounded attitudes loses their common initial rotation. Because
the reference force is near gravity in magnitude, that lost cancellation can
recreate the original broad remainder.

Preserve the exact factors `R=Q*R_initial*P`, where `Q` accumulates the left
navigation rotations and `P` the right body rotations. Track `E_Q=Q-I` and
`E_P=P-I` directly. For a small left increment `E_step=exp(-win*dt)-I`,

`E_Q_new=E_Q+E_step+E_step*E_Q`.

For a right body increment `E_body=exp(theta)-I`,

`E_P_new=E_P+E_body+E_P*E_body`.

An exponential-minus-identity has the same derivative/remainder as the original
exponential, but a small center norm. Reconstruct complete rotation matrices
with the known rotation norm when required. At a half step, build the analogous
`Q_mid/P_mid` from the same old state and the native half increments. Then

`force_rest=E_Q_mid*R_initial*P_mid*f_reference`
`           +R_initial*E_P_mid*f_reference`
`           +R_mid*(f_current-f_reference)`.

This exact identity keeps relative-attitude changes small without declaring
aircraft motion zero. Common force-bias cancellation must be algebraic, as in
the component plan. Every calibration column stays present.

## Accumulate departures from the reference velocity

Maintain `v=v_initial+A*S+u`, where `S` is the common accumulated period and
`u` contains all departures. For the native skew argument
`a=(dt/2)*(2*earth+transport)` and `B=(I+[a]x)^-1`, the exact residual increment is

`du=B*(dt*force_rest-2*(a cross v)-dt*(a cross A))`.

The complete increment is `A*dt+du`. The last term follows from
`(B-I)A=-B*(a cross A)`; omitting it changes the model. Gravity is already in
the reference `A`; do not add it a second time. Field removal affects the same
navigation-rate terms as in the unchanged engine.

Follow the existing two-context midpoint construction: first estimate an
increment using transport at the provisional midpoint, then derive revised
coordinate rates from the midpoint of the old velocity and that **estimate**.
Use those revised rates for the final transport/increment. Do not substitute an
average involving the final corrected velocity.

At that midpoint, use the reference velocity
`v_initial+A*(S_previous+dt/2)` and residual `u_previous+du_estimate/2`.
For fixed initial metric `m0` and current midpoint metric `m`, split rates into

`m0*v_initial + m0*A*S_mid`
`+ m*u_mid + (m-m0)*(v_initial+A*S_mid)`.

Integrate only the last two terms as departures. The constant-reference terms
sum exactly to `m0*(v_initial*S + A*S*S/2)`. Use the correlated prefix clock;
do not accumulate independent quadratic time errors. Initial-velocity scalar
bounds retain their per-axis domains, as in the previous candidate.

Intermediate position/velocity/metric bounds must include the complete common
errors. Their indirect influence on transport, gravity-frame rotation and
geographic denominators cannot be removed by final observation factorization.

## Factor only the final observation

Use the qualified acceleration component's three common vectors and the clock
center `s`, native slope `q`, and remainder `e`. The acceleration polynomial's
unshared allowance retains

`A_max*((abs(s)+abs(q)*delta_tau_max)*e_max + e_max*e_max/2)`.

Its nine coefficients are the known fixed metric times `q*q`, `s*q` and
`s*s/2`, with the component's normalization radii. Keep the prior six
velocity/time and initial-lever columns. All epochs use one source-bound
15-vector; no block can be dropped or independently reselected per epoch.

The lever can use the same relative factors:

`(R-R_initial)L=E_Q*R_initial*P*L+R_initial*E_P*L`.

Retain metric/lever cross terms and the existing initial-lever common error.
This also avoids bounding a small attitude departure by the sum of two large
initial-attitude uncertainties.

## Tests and next gate

First use independent constant-force/constant-velocity controls where the
reference polynomial is exact, including nonzero actual levers, offset signs
and calibration centers. Compare centers and all 27 tangent columns against
the unchanged native engine for every model/processing case. Check actual known
control common vectors against the new unshared remainder at corners and fixed
interior points. Include packet boundaries and clock slopes other than one.

Retain the existing 1 micrometre center/pose, 20 micrometre tangent-column and
10 micrometre arithmetic comparison limits unless a separate justified method
specifies a genuinely different question. Do not relax them to obtain success.
No complete floating-point enclosure follows from numerical agreement alone.

Next qualify a typed 42-column joint interface with complete source/domain/
expansion bindings and future-truth isolation, then freeze a matched complete
orientation-cover comparison. Short correctness and usefulness do not establish
recording-scale uncertainty, receiver-error adequacy or independent confirmation.

[Component controls](../ilvis0-reference-acceleration-controls/INTERPRETATION.md) ·
[Common-error identity](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
