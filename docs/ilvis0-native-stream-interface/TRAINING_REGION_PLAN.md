# Training information may narrow the prediction region

The affine contractor is implemented and all **10 component tests pass**,
including exact-rational feasible-point checks, signed/zero columns, near-touching
bounds and overflow rejection. A separately frozen finite qualification is next;
no native uncertainty box has been narrowed by these tests.

The connected native source passes all 24 frozen interface controls. Useful
recording-scale nonlinear bounds remain the limiting requirement. A small
calibration box chosen around a fitted answer is not automatically a valid
replacement for the full declared parameter region.

The next mathematical prerequisite contracts a box using **necessary** training
constraints while retaining every nuisance coordinate. For an approximation
`f(theta) = f0 + J*(theta-center) + remainder`, observations `y`, componentwise
measurement allowances `e` and valid global remainder bounds `r` imply

\[
y-f_0+J\,center-e-r\leq J\theta
\leq y-f_0+J\,center+e+r.
\]

Each row provides conservative bounds for a coordinate by allowing every other
coordinate to vary over its entire current interval. Intersect those bounds
with the old box and repeat a finite number of times. Use outward arithmetic;
preserve zero/unidentified columns. A contradiction may exclude a box only when
its entire outward row interval misses the necessary constraint. Lack of
contraction is a valid outcome, not a reason to delete a parameter.

## Implementation and qualification

- `lll.ilvis0_training_box` is a pure affine-constraint component. It accepts
  a full box, matrix and lower/upper row constraints. It reads no archive,
  performs no native integration or fitting, and makes no scientific decision.
- Check exact known intervals, contradictory rows, all 27 columns, signed and
  zero coefficients, nearly touching boundaries and finite iteration limits.
  Compare retained feasible points with an independent exact-rational oracle.
- An outward overflow or unsupported domain must fail, not silently clip away
  possibilities. Return unresolved width honestly when the constraints are weak.
- After these tests, freeze a finite generated qualification before applying
  any contraction to a native prediction uncertainty construction.

## What this does not supply

This calculation cannot establish the measurement allowances, global nonlinear
remainders or native floating-point error. Those must be valid over each input
box. Any statistical coverage comes from a separately justified training-noise
event and shared scale, not from interval contraction itself. If every true
parameter satisfies the input inequalities on that event, conservative repeated
intersection preserves that same event; it does not create another independent
confidence claim.

If the full-box remainder makes the inequalities uninformative, this step may
leave the box unchanged. Supported short-prefix constraints, separate branches
or tighter global propagation would then be needed. No observed fit or protected
ESA outcome is authorized by a successful affine software control.

[Native interface](README.md) · [Recording-scale limitation](../ilvis0-recording-scale-bounds/INTERPRETATION.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
