# Rounded source bounds with saved training constraints

**6/6 generated-source comparisons passed.**

| Candidate / removal | Result | Body bounds | Known-calibration checks |
|---|---|---:|---:|
| Globe with specified field / zero | Passed | 20 | 240 |
| Globe with specified field / profiled | Passed | 20 | 240 |
| Globe with zero field / zero | Passed | 20 | 240 |
| Globe with zero field / profiled | Passed | 20 | 240 |
| Flat disc / zero | Passed | 20 | 240 |
| Flat disc / profiled | Passed | 20 | 240 |

Charged 6/6 complete physical bounds and 19200/19,200 bound steps. Reserved 19,200/19,200 compiled source steps, 36/36 training supports, 120/120 rounded body bounds and 1,440/1,440 known-calibration comparisons. Elapsed 56.90 seconds.

The bounds retain the original training certificates, physical domains, stated centers and all 27 affine columns. The reference bridge checks the existing nonlinear cap without expanding it. Physical norm closure precedes conversion to numerical centers. Known calibrations are inspected only after all selected bounds have been sealed. Value and affine-error comparisons use no added numerical margin.

This is generated-data component qualification. It does not qualify complete native position propagation, useful prediction widths or calibrated observation-error coverage. No aircraft fit, full native trajectory, protected ESA data or optimizer was used. Earlier point failures remain preserved in their original implementation.

[Frozen scope](PLAN.md) · [Physical source qualification](../ilvis0-source-value-controls/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
