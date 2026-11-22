# The shape ranking transfers within one flight, while the calibration does not improve the fit

The globe had lower later direction error in **all 48 matched settings**
across eight disjoint windows of the opened ESA flight. This held both
with nominal calibration and with the pooled calibration carried over
from an earlier window. The transferred calibration **increased** the
globe's later error in all 16 settings where the gyro retained the
specified field. The increase ranged from **2.3 to 10.1 times**, with a
median of **4.6 times**.

| Window type and gyro field assumption | Globe median RMS, nominal / transferred | Disc median RMS, nominal / transferred | Globe advantage after transfer |
| --- | ---: | ---: | ---: |
| Straight-course, zero field in both | 0.376° / 0.319° | 0.521° / 0.462° | 0.140–0.209° |
| Straight-course, specified field retained | 0.0055° / 0.0373° | 0.148° / 0.106° | 0.060–0.155° |
| Straight-course, specified field removed from gyro | 0.376° / 0.319° | 0.521° / 0.461° | 0.137–0.218° |
| Turning, zero field in both | 0.360° / 0.313° | 0.508° / 0.451° | 0.085–0.147° |
| Turning, specified field retained | 0.0043° / 0.0259° | 0.152° / 0.105° | 0.045–0.092° |
| Turning, specified field removed from gyro | 0.365° / 0.313° | 0.511° / 0.450° | 0.089–0.147° |

Each row covers four windows and two averaging widths. The last column
reports paired disc-minus-globe RMS differences. The fits that set the
calibration were finished before these windows were scored. In each new
window only the starting orientation was estimated from the first eight
force directions. The next eight directions were then scored at fixed
calibration and orientation. The comparison uses the receiver export
velocities on all eight windows.

The transferred calibration also increased the earlier error in all 16
retained-field globe settings, by a median factor of 2.9. Removing any
two consecutive later directions preserved the shape ranking at both
calibrations. All 672 such checks use the same fitted starting
orientations and overlapping observations.

The window results narrow the interpretation of the pooled fit. Its lower
earlier loss did not translate into better retained-field globe directions
elsewhere in the flight. That difference can reflect calibration drift,
receiver errors, motion or limitations in the model. The test does not
separate those effects or establish an aircraft direction-error range.
The eight windows are from one flight and do not supply independent
confirmation.

All eight tasks passed the packet and scoring checks. The study used 104
packet passes and no new sensor calibration search, original data-file
read, original position holdout or reserved group.

## Recompute the public tables

From the repository root, run the checker with standard Python. It checks
the report hashes and recomputes the RMS tables, calibration error ratios
and direction omission checks from the saved angles alone.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_direction_evidence
```

## Verify the local study

Restore the closed `data/esa-direction-window-transfer-v1` study and run
the report command to verify its records without replaying the packets.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_direction_window_transfer report
```

[Frozen design](ESA_DIRECTION_WINDOW_TRANSFER_PLAN.md) ·
[All windows, errors and packet charges](esa-direction-window-transfer-result.json)
