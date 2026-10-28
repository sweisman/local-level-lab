# The bounded timing proposals pass their physical checks

All **18 saved proposals** meet the original cost, stationarity and
position-change limits when evaluated in the unchanged physical calculation.
The complete run takes **2.6 minutes**, using 26 residual/Jacobian evaluations
across four existing generated-data examples. The implementation passes 103
software checks before execution.

## What changed

The earlier smooth correction crossed a point where the timing derivative
changes. It predicted a small improvement but actually increased the error.
The replacement proposals keep each linear step inside its timing interval,
while retaining all 27 calibration and timing coordinates.

This test evaluates every saved proposal, on every feasible side and at every
saved spacing. It does not choose only the best-looking proposal.

| Existing example | Proposals checked | Largest relative cost change | Largest position change |
|---|---:|---:|---:|
| Passing control, first start | 3 | 3.75 × 10⁻¹³ | 1.42 micrometres |
| Passing control, second start | 3 | 3.77 × 10⁻¹³ | 1.46 micrometres |
| Previously failed example, first start | 6 | 2.01 × 10⁻¹¹ | 0.72 micrometres |
| Previously failed example, second start | 6 | 6.22 × 10⁻¹³ | 1.10 micrometres |

All proposals for the two failed examples slightly reduce the actual cost.
The original cost-change limit is 10⁻⁸; the position limits are 1 millimetre RMS
and 1 centimetre maximum per coordinate. Every proposal also passes the original
stationarity screen. The source inputs, training observations, error operators,
baseline residuals and complete Jacobians reproduce exactly.

## What remains

These results qualify the fixed-point proposals, not a complete optimizer.
The next step is to integrate the interval-constrained component into a finite
optimizer and test it on independently specified known optima and non-optima,
including repeated starts. Earlier failed-fit labels remain unchanged.

No aircraft observation was fitted, no protected group was inspected, and no
calibration campaign was restarted. Both completed calibration campaigns and
their unused allowances remain closed. This numerical result adds no aircraft
comparison or statistical confidence claim to the 53-stretch findings.

[All proposal measurements](proposals.csv) · [Point summary](results.csv) ·
[Frozen method and allowance](PLAN.md) · [Reproduction record](README.md) ·
[Next analyses](../NEXT_STEPS.md).
