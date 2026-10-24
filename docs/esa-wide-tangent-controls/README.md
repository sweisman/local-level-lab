# Wider-precision long motion controls

**48/48 known-answer cases pass.**

The twenty-minute generated tracks turn and climb or descend. All three
physical models, both latitude signs, both processing cases and both gravity
laws are retained. Initial state and calibration are supplied, not fitted.
The unchanged value calculation and the wider tangent retain all 27 columns.

| Check | Largest error |
|---|---:|
| 300 Hz spatial error | 0.109017 m |
| 600 Hz spatial error | 0.0272524 m |
| Value/tangent agreement | 3.82886e-05 m |

This is not a solver qualification. It checks known motion and corrections;
calibration estimation and stopping still need their own matched controls.
No aircraft recording or protected confirmation group is opened.

The run charged 144 native calls in 38.87 minutes.
[Frozen plan](PLAN.md) · [Precision diagnostic](../esa-precision-diagnostic/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
