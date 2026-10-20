# Candidate: preserve a common reference acceleration

This is a proposed continuation if the duration screen confirms that position
propagation dominates the remaining allowance. It authorizes no new observed
fits. Preserve the completed shared-reference comparison and its source freeze.

## Exact physical split

At the fixed joint expansion, choose one recorded reference specific-force
sample. For a physical calibration vector `p`, define a constant navigation-frame
reference acceleration

`A(p) = R_initial(p) * f_reference(p) + g(p) * e_down`.

This is an algebraic reference term, not an additional measured force or an
assumption of constant actual aircraft acceleration. Keep every departure from
it. In particular,

`R_mid f_current = R_initial f_reference`
`                  + (R_mid - R_initial) f_reference`
`                  + R_mid (f_current - f_reference)`.

For a common bias/gain calibration, the force difference has exact cancellation
of the common additive bias:

`f_current - f_reference = (raw_rate_current - raw_rate_reference) / (1 + gain)`.

Do not bound two independent bias terms and subtract their radii. Differences
must use the declared incremental-velocity periods without interpolating data.
Bound the attitude difference by accumulated physical rotation, retaining field,
transport and calibration effects. Preserve supported gain domains.

The midpoint velocity equation also contains `B=(I+[a]x)^-1`. Splitting off
`A * period` requires retaining `(B-I) A`, using the exact identity
`(B-I) A = -B (a cross A)`, and the existing force, gravity, Coriolis and
transport remainders. Keep the native predictor's estimate-based midpoint;
substituting a midpoint of the final corrected velocity changes its model.

Accumulate velocity departures from `v_initial + A*S` directly. Split coordinate
rates with a fixed reference metric, retaining every changing-metric term. The
constant-acceleration contribution to position is `A*S*S/2`; do not independently
widen the same time/acceleration at every packet. Intermediate state bounds must
retain the complete common errors and their indirect effects on geographic
metrics and dynamics.

## One polynomial of common errors

Let `c` be the fixed expansion, `delta_tau=tau(p)-tau(c)`,
`A_c=A(c)` and `gamma_A=A(p)-A_c-J_A*(p-c)`.
At a query the correlated clock is `S=s+q*delta_tau+e`, with known center `s`,
known native slope `q` and a separately bounded clock remainder `e`.
The exact nonlinear part of `A*(s+q*delta_tau)^2/2` after its physical tangent is

`(s*s/2) * gamma_A`
`+ (s*q) * ((A-A_c)*delta_tau)`
`+ (q*q) * (A*delta_tau*delta_tau/2)`.

These are **three common three-vectors**, shared across every epoch, with known
query-dependent coefficients. Do not force `q=1` at packet boundaries. Retain
the full extra clock contribution; a norm bound is

`A_max * ((abs(s) + abs(q)*delta_tau_max)*e_max + e_max*e_max/2)`.

The previous velocity/time and initial-lever error blocks remain. A direct
construction therefore has 27 physical plus 15 auxiliary enclosure coordinates.
These auxiliaries are conservative mathematical error variables, not new sensor
freedoms; one fixed source/domain/expansion binding must link all epochs.

Obtain bounds for the three new vectors from the original complete calibration
domain: the reference acceleration's Taylor remainder, its full change times
the time-offset radius, and half its full norm times the squared time-offset
radius. Use outward arithmetic and independently validate the actual nonlinear
vectors, including nonzero force/attitude/gain/bias/time centers. An unknown
aircraft calibration is never supplied to the region calculation as an oracle.

## Qualification sequence

1. Independently test the polynomial identity and conservative radii, including
   packet slopes zero/one/two, negative offsets and clock remainder.
2. Build a separate native candidate from the algebra above. Keep original
   physical models, parameter bounds, packet handling and reference source.
3. Qualify native values, every physical tangent column and factored probe
   residuals on all candidates/processing cases, independent constant-motion
   controls, nonzero centers and genuine nonzero levers.
4. Qualify the expanded joint interface: all columns and one common block across
   training/future, exact support certificates, binding/domain rejection and
   future-truth isolation.
5. Freeze a matched usefulness comparison separately. A shorter or correct bound
   alone cannot qualify recording-scale prediction or observational uncertainty.

Every new numerical study needs its own finite frozen allowance. No retries,
completed-budget reuse, altered acceptance limits, process signals or protected
ESA evaluation. Whole-program floating-point enclosure and receiver-error
adequacy remain separate requirements.

[Duration screen](../ilvis0-shared-duration-growth/PLAN.md) ·
[Completed short comparison](../ilvis0-shared-cover/INTERPRETATION.md) ·
[Canonical roadmap](../ANALYSIS_ROADMAP.md).
