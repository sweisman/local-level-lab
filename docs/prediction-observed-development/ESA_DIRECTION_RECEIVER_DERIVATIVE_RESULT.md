# The direction ranking survives changes in receiver and derivative method

The globe gave lower error in **all 576 direction comparisons** on the
eight open ESA windows, including **all 192 with zero background field
in both shapes**. The test used three receiver products, two averaging
widths and both the position-derived and velocity-derived predictions.
The measured angles use the same logged gyro data throughout.
[Original direction comparison](ESA_DIRECTION_ANGLE_PAIRS_RESULT.md)

| Receiver derivative method | Antenna offset applied | Globe has lower error | Smallest globe advantage |
| --- | --- | ---: | ---: |
| Reported velocity | No | 144 of 144 | 0.00070° |
| Reported velocity | Yes | 144 of 144 | 0.01616° |
| Positions | No | 144 of 144 | 0.00362° |
| Positions | Yes | 144 of 144 | 0.00347° |

The globe advantage is the disc's angular RMS error minus the globe's.
Switching derivatives changed the predicted angle sets by a median
**0.0209° RMS**, compared with **0.0012°** when switching from the primary
receiver to either of the other two products. The worst change from
switching derivatives was **1.017°** on the first straight-course
window. With position derivatives, both shapes can miss the measured
angles by about a degree on that window while keeping the same order.
When the specified field is retained and the antenna offset is applied,
the median globe error is 0.0038° using reported velocity and 0.0173°
using position derivatives.

The largest difference in estimated acceleration occurs at receiver
index 262 on the first straight-course window with the 25-report
kernel. The difference in north acceleration is 0.341–0.342 m/s² across
the three products. Reconstructing a position path by trapezoidal
integration of the reported velocity, then applying the cubic position
derivative, accounts for 0.337–0.338 m/s² of that difference. This
saved-input check points to the derivative methods' different responses
to motion on that support. It leaves the true aircraft acceleration
and any error in the reported velocities open.

These scores compare the measured direction changes with predictions
using the recorded receiver trajectories. The three products share an
antenna, and the 576 comparisons reuse eight windows of a single flight.
Separate-flight verification and absolute error calibration remain open.
The [force magnitude comparison](ESA_FORCE_POSITION_DERIVATIVE_RESULT.md)
leaves shape unresolved when the measured direction changes are omitted.

All eight tasks passed. The primary velocity-based predictions reproduced
the original angles and both antenna-offset scores. The study charged
522,240 quadrature points and reused the saved measurements throughout.
[Frozen design](ESA_DIRECTION_RECEIVER_DERIVATIVE_PLAN.md) ·
[Predicted angles, scores and charges](esa-direction-receiver-derivative-result.json)

To verify the saved report, restore
`data/esa-direction-receiver-derivative-v1` and run this command.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_direction_receiver_derivative report
```
