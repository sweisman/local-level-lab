# Feasible scalar matches resolve the calibration-control gate

The new candidate passes **all 12 known-answer identities and all 72 matched
three-start comparisons**. It uses the same constructed histories, seven
calibration bounds and repeat tolerances as the earlier nonlinear study.
That study's failed outcomes remain unchanged.

The batch completed 228 charged identities in 11.57 seconds: **147 algebraic
certificates and 81 actual mathematical optimizer starts**, using 4,950 counted
residual/Jacobian calls. It read no aircraft originals, ran no observed fit and
performed no native integration.

## Why this works

Before optimizing, the new candidate asks whether one feasible constant gain
already matches the complete scalar history. It checks every epoch, all gain
bounds, fresh residuals and the full seven-column Jacobian. A matching mean alone
is insufficient; a gain outside the bounds is rejected without clipping.

Forty-eight of the 72 constructed histories have such a near-zero scalar match.
Their three requested starts therefore return explicitly labeled feasible
constructions, not three claims of independent optimizer convergence. Across
all certificate identities, maximum RMS is about 1.35 × 10⁻¹⁴ m/s². The largest
feasible objective is 1.11 × 10⁻²⁶, against a nonnegative lower bound of zero.
This does not claim unique calibration or an exact global optimum.

The other 24 histories are wrong-model changing-direction and climbing controls.
They use the unchanged bounded solver from each requested start and pass all
repeat checks. The construction does not force a model difference or require
one for software qualification.

## What this establishes

The scalar-calibration software now handles both informative and nearly
uninformative controls without asking a nonlinear optimizer to rediscover an
already available feasible solution. The unit checks also reject temporal
disagreements hidden by a mean match and physically inadmissible gains.

This qualifies **C02's mathematical diagnostic**, not an observational error
model or independent detection of curvature. A scalar match supplies only a
necessary constraint: it does not identify orientation or demonstrate a complete
motion history without gyroscopes. Actual observations may remain ambiguous.

C03's quantization, synchronization, integration-period, within-packet motion,
receiver-differentiation and combined uncertainty gates still precede recorded-data
channel comparisons. C04 remains blocked by those gates. The main result remains
**53 globe / zero flat / zero unresolved**, and the separate IMU21 horizontal-only
sensitivity outcome remains unresolved.

[Every identity](starts.csv) · [Completed report](README.md) · [Frozen plan](PLAN.md) ·
[Earlier failed method](../ilvis0-scalar-nonlinear-controls-20261019/INTERPRETATION.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
