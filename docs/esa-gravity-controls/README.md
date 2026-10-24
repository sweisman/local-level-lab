# Gravity controls during climbs and descents

**48/48 generated cases pass the frozen checks.** The tested known-correction calculation qualifies.

These twenty-minute tracks are generated independently from analytic Cartesian geometry.
They climb or descend through 2 km while turning. All three candidates, both latitude signs,
both removal cases and both gravity laws are retained. Initial state and sensor/antenna
corrections are supplied exactly; no calibration is fitted.

| Gravity assumption | Passed | Largest 300 Hz spatial error | Largest 600 Hz spatial error | Value/derivative disagreement |
|---|---:|---:|---:|---:|
| Constant magnitude | 24/24 | 0.0926228 m | 0.0231554 m | 5.23187e-09 m |
| Declared height dependence | 24/24 | 0.109017 m | 0.0272524 m | 1.17957e-08 m |

Each resolution must meet horizontal and height RMS ≤1 m and maximum spatial error ≤5 m.
The finer maximum must be at most 0.4 times the coarse maximum plus 0.001 m.
Value and derivative predictions must agree within 0.001 m, retaining all 27 nuisance columns.
These are software acceptance targets, not measured instrument precision or calibrated uncertainty.

The run charges 144 native calls in 17.17 minutes.
Construction journals retain 51,840,000 increments and 51,841,968 generated samples.
The saved-only audit checks hashes, complete physical errors, derivatives, labels and charges.
It does not generate truth again, propagate, fit or open an original recording.

The height-dependent law is the same declared force-law sensitivity for every geometry.
It does not provide independent curvature evidence or establish the cause of the ESA pilot errors.
Longer training-only calibration and forecast controls remain necessary before a revised observed fit.
Seven ESA confirmation groups and the original NASA results remain unchanged.

[Frozen question and limits](PLAN.md) · [Implementation](IMPLEMENTATION.md) · [Saved-data diagnosis](../esa-development-diagnosis/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md)
