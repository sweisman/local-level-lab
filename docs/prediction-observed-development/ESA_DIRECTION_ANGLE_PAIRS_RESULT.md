# The direction changes favor the globe without a fitted starting orientation

On eight windows of one ESA development flight, the globe predicted
changes in force direction more closely than the disc in **all 48
comparisons**. This includes 16 settings with the background field set to
zero for both shapes. All use the nominal sensor calibration.

The gyroscope puts accelerometer measurements from different times into
one frame. The receiver trajectory supplies the predicted force directions
for each model. We compare the angles between each pair of the eight later
directions. A common rotation of the frame leaves those angles unchanged,
so the comparison needs no fitted starting orientation. Each setting uses
28 angles, and many share the same direction measurements.

| Windows and field assumption | Globe median RMS | Disc median RMS | Paired globe advantage |
| --- | ---: | ---: | ---: |
| Straight-course, zero field in both | 0.1158° | 0.1561° | 0.0149–0.0421° |
| Straight-course, specified field retained | 0.0044° | 0.0530° | 0.0007–0.0558° |
| Straight-course, specified field removed from gyro | 0.1156° | 0.1558° | 0.0164–0.0418° |
| Turning, zero field in both | 0.1166° | 0.1447° | 0.0192–0.0408° |
| Turning, specified field retained | 0.0031° | 0.0455° | 0.0303–0.0603° |
| Turning, specified field removed from gyro | 0.1170° | 0.1451° | 0.0192–0.0409° |

Each row covers four windows and two averaging widths. The last column
gives the disc RMS minus the globe RMS within each matched setting. The
smallest margin is 0.0007°. This check removes dependence on a fitted
starting orientation. Receiver and instrument errors still need to be
measured across independent flights.

With both predicted angle sets fixed, the closest tie in these scores
requires an RMS change of at least **0.00167°** in the measured pair angles
with the specified field retained. The smallest corresponding changes
are **0.04525°** with zero field in both models and **0.04862°** with the
specified field removed from the logged gyro. These are distances to a
tie when the angles can vary freely. Real errors affect several angles
together and may also change the predicted directions through the
receiver trajectory. The distances do not estimate the size of either
kind of error.

To reproduce the distances from the saved table, subtract the squared
globe RMS from the squared disc RMS for each setting, then divide by
twice the RMS difference between the two sets of predicted angles.

All eight tasks reproduced the saved nominal aligned scores as a separate
check and then scored the angles. Each task replayed 119,715 intervals,
for 957,720 total. The study used archived inputs and opened no reserved
flight group. [Frozen design](ESA_DIRECTION_ANGLE_PAIRS_PLAN.md) ·
[All measured and predicted angles](esa-direction-angle-pairs-result.json)

## Recompute the public tables

From the repository root, run the checker with standard Python. It checks
the three report hashes and recomputes the RMS tables and distances to a tie
from their saved angles. It needs neither the original recordings nor the
local study catalog.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_direction_evidence
```

## Verify the local study

Restore the closed `data/esa-direction-angle-pairs-v1` study and run
the report command to check the saved evidence without replaying the packets.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_direction_angle_pairs report
```
