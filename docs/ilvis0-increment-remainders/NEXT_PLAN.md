# Bound the actual midpoint local step

The completed component study covers reciprocal calibration, rotations and
fixed-time body preintegration. Continue with the actual local step in
`ilvis0_native.c` and `ilvis0_tangent.cpp`, without changing either frozen kernel.
No observed-data prediction starts follow from the component pass.

## Local dynamics

For skew matrix `S(a)`, the native velocity update uses
`B(a) = (I + S(a))^-1` and `T(a) = B(a)*(I - S(a)) = 2*B(a)-I`.
`B` has operator norm at most one; `T` is orthogonal. The resolvent identity
gives global first-derivative/Taylor constants of 1/1 for B and 2/2 for T.
Include vector-product remainders, rather than treating these factors as fixed.

The midpoint force rotation is
`Exp(-win*dt/2) * attitude * Exp(theta/2) * dv`, while final attitude uses
full rotations. Propagate both rotation products with their orthogonality intact.
The local velocity update combines `T(a)*v` with `B(a)*(force + gravity*dt)`.

Preserve the native processing distinction:

- `win = physical_background + transport - removal*standard_background`;
- `a = (2*physical_background + transport)*dt/2`.

Removal changes the logged-rate interpretation, not the physical Coriolis term.
The conventional standard vector is the same for every candidate, including
the stationary disc. Do not replace it with a candidate-specific field.

## Qualification and remaining closure

Start with independent linear algebra/exponential references and supplied
global vector/matrix input bounds. Test large attitude changes, joint force/
rate uncertainty, both hemispheres, all three candidate field assignments,
zero/profiled removal and nearly zero rates. Check every nominal value and
directional derivative before qualifying a separately frozen finite matrix.

Then construct global geographic-rate/context bounds from a supported state
region and propagate the predictor/corrector step as actually coded. Domain
crossings must be unsupported, not clipped. Receiver-time uncertainty across
packet boundaries and long-record floating-point effects remain separate.

These are prerequisites to a complete native global bound. Local software
success cannot itself calibrate the receiver error family or authorize a
new observed prediction study.

[Completed components](INTERPRETATION.md) ·
[Training-only interface](../ilvis0-bounded-prediction-controls/NATIVE_INTERFACE.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
