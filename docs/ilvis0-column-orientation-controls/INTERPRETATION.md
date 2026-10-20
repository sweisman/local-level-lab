# Separate column-motion bounds pass their controls

All 24 controls passed in 22.7 seconds, covering 1,536 physical probes and
119,808 new support checks. The reused independent rotation/force oracle agreed
with the component to within 1.42 × 10⁻¹⁵.

The new bound accounts for how each matrix column responds to rotation about
its own axis and perpendicular axes. Its derivation uses the matrix-exponential
derivative, not just the sampled controls. Local tests check pure axial and
mixed-axis rotations, point domains and a contracted column admitted by the
previous common-distance bound.

All original physical bounds and 51 coordinates remain. The calculation uses
no original aircraft records, native integrations or new bounds. The separate
[saved comparison](../ilvis0-column-orientation-prediction/PLAN.md) tests complete
prediction ranges; software correctness alone does not establish usefulness,
whole-program numerical enclosure or aircraft error coverage.

[Results](README.md) · [Frozen derivation](PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
