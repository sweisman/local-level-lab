# Earlier force directions predict later ones best for the globe at nominal calibration

With nominal instrument calibration, the globe gives smaller angular
errors than the disc in every matched field setting. With the specified
field retained in the gyro, the globe's later error is **0.004–0.011° RMS**
versus **0.124–0.133°** for the disc. A **+0.10 m/s² X-axis accelerometer
bias correction** reverses that ranking in all six receiver and averaging
combinations for this field setting.

| Matched background assumption | Nominal globe / disc later RMS | Globe / disc later RMS with +0.10 m/s² X correction |
| --- | ---: | ---: |
| Zero in both models | 0.314–0.328° / 0.440–0.460° | 0.270–0.286° / 0.378–0.402° |
| Specified field retained in gyro | 0.004–0.011° / 0.124–0.133° | 0.124–0.128° / 0.102–0.109° |
| Specified field removed from gyro | 0.316–0.330° / 0.442–0.462° | 0.271–0.289° / 0.379–0.404° |

The gyro brings the accelerometer directions into one common frame.
Each model gets one starting-frame rotation estimated on the first eight
directions. That rotation then predicts eight later directions without
realignment. The five X-bias values and three field cases were fixed
before scoring. All 180 alignments passed the numerical geometry screen.
Rotation about the main force axis remained weakly constrained in the
earlier data. The smallest ratio of weakest to strongest rotation
information was about 0.00043.

This extends the [paired-angle result](ESA_MATCHED_GYRO_DIRECTION_RESULT.md)
to an earlier-only alignment followed by later direction scoring. It also
reproduces the [calibration sensitivity](ESA_GYRO_DIRECTION_CALIBRATION_RESULT.md)
using the whole set of directions. The zero-field comparison favors the
globe in every tested X-bias case, with much larger absolute errors than
the nominal retained-field globe. The analysis gives no calibrated
accuracy threshold and does not establish which calibration describes
the aircraft instrument. All supports come from one already opened flight.
The later eight directions were withheld from the alignment only. The
original position forecast's 120 later receiver reports and all seven
reserved flight groups stayed closed. No full inertial fit ran.

## Reproduce the results

With the closed `data/esa-force-direction-transfer-v1` study restored,
run the saved-report command. It verifies the complete charge record and
reads the sealed direction scores without recalculating inertial motion.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_force_direction_transfer report
```

[Frozen design](ESA_FORCE_DIRECTION_TRANSFER_PLAN.md) ·
[All 90 paired comparisons and angular errors](esa-force-direction-transfer-result.json)
