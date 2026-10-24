# Wider-precision training and prediction controls

**24/24 generated fits pass all frozen checks.**

Earlier 800 receiver positions determine initialization, calibration and the
gravity anchor. Later 400 positions score a continuous forecast only after
it is saved. True initial state and calibration are not supplied. Both starts,
both processing cases and both working error assumptions remain in the test.

The existing procedure supplies the same fit allowance and stopping checks.
Only its explicitly bound problem factory uses the wider calculation.

| Later prediction check | Largest error |
|---|---:|
| Horizontal RMS | 8.70127e-06 m |
| Height RMS | 3.11612e-06 m |
| Spatial maximum | 1.88789e-05 m |

These are generated software controls, not aircraft findings or calibrated
confidence. No protected confirmation flight is opened. All original fit
labels remain unchanged. A revised observed study needs its own freeze.

The run charged 268 native calls in 113.96 minutes.
[Frozen plan](PLAN.md) · [Known-motion gate](../esa-wide-tangent-controls/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
