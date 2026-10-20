# Orientation-aware matrix constraints pass their controls

All 24 generated controls passed in 26.0 seconds. They checked 1,536 physical
probes and 119,808 new support inequalities. The reused independent rotation/force
oracle agreed with the supplied component to within 1.42 × 10⁻¹⁵.

The constraints retain the declared range of orientation rather than allowing
each matrix column to point anywhere. They preserve all original physical bounds
and all 51 coordinates. A local test excludes a contracted column admitted by
the older full-sphere constraints while retaining tested physical calibrations.

Signed gain bounds matter: a positive support uses a reciprocal upper chord;
a negative support uses a lower tangent before multiplication by the negative
value. The center rotation and its error allowance use the existing exact
polynomial construction. Coefficients are exported outward.

This is software qualification, not an aircraft finding. No original recordings,
native integrations or bounds were evaluated. The separately frozen
[saved prediction comparison](../ilvis0-orientation-gain-prediction/PLAN.md)
tests whether these constraints materially narrow useful ranges. Full physical
realizability, recording-scale usefulness and observational coverage remain open.

[Results](README.md) · [Frozen derivation and allowance](PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
