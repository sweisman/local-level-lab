# Axis-specific calibration reduced the gaps of some force comparisons

All **32** training-only proposals completed and were checked using the
original accelerometer counts. Every proposal left some training
intervals apart after applying the exact nonlinear correction. The best
results came from proposals using the narrow calibration box and the
fourth-degree GPS paths.

| Calibration box | GPS trajectory | Range of exact training gaps | Range of exact later gaps |
|---|---|---:|---:|
| Narrow | Quadratic | 0.0444–0.0510 m/s² | 0.0422–0.0526 m/s² |
| Wide | Quadratic | 0.0518–0.0632 m/s² | 0.0497–0.0616 m/s² |
| Narrow | Fourth-degree | 0.00716–0.0171 m/s² | 0.00415–0.00642 m/s² |
| Wide | Fourth-degree | 0.0143–0.0293 m/s² | 0.0127–0.0186 m/s² |

Every proposal put at least one parameter at its allowed limit. On the
same training cases, the linear and exact gaps differed by as much
as 0.0137 m/s². The wider box gave poorer **proposals** in this test. It
contains the narrower box, so its best possible nonlinear fit could still
be at least as good. The comparison checks one proposal per case and cannot
exclude other calibrations.

The [frozen plan](AXIS_FORCE_PILOT_PLAN.md) applies one signed gain and offset
per axis across both GPS paths and both clocks. The later comparison uses
the saved training correction without changes. The measured intervals
describe packet-averaged force. Common GPS errors and continuous force
direction remain open.

[All 32 results](axis-force-pilot-receipt.json) ·
[Archived inputs and method](../ilvis0-axis-force-pilot-runtime/README.md).

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.ilvis0_axis_force_pilot_report
```
