# A small gain change cleared the training force lower bounds

All four candidates passed the training inequalities after applying one
common gain correction per recorder and candidate. Every correction was
below **1%**, within the existing 15% allowance. The corrections were then
held fixed for the later comparison. All four cases still cleared the IMU21
lower bounds. All four had a small number of later violations on IMU8.

| Recorder | Candidate | Training gain | Later violations at zero gain | Later violations with the gain held fixed |
|---|---|---:|---:|---:|
| IMU8 | Globe, specified field | 0.385% | 414 | 6 / 1,158 |
| IMU8 | Globe, zero field | 0.243% | 201 | 6 / 1,158 |
| IMU8 | Disc, specified field | 0.964% | 1,085 | 14 / 1,158 |
| IMU8 | Disc, zero field | 0.135% | 89 | 8 / 1,158 |
| IMU21 | Globe, specified field | 0.162% | 18 | 0 / 708 |
| IMU21 | Globe, zero field | 0.155% | 18 | 0 / 708 |
| IMU21 | Disc, specified field | 0.106% | 18 | 0 / 708 |
| IMU21 | Disc, zero field | 0.071% | 12 | 0 / 708 |

The largest remaining excess on IMU8 was 0.00772 m/s². These are overlapping
windows evaluated under two clocks and three GPS processing choices. The
row counts describe checks on two recordings. They cannot establish accuracy
or independent replication across flights.

The [frozen test](MATCHED_FORCE_GAIN_PLAN.md) uses only a lower bound from
the recorded accelerometer and an upper bound from the GPS-predicted force
over the same intervals. Passing leaves the full force and orientation
history unresolved. The IMU8 violations show where this particular gain
choice and GPS path bounds fall short. A calibrated comparison still needs
receiver, calibration and trajectory errors handled jointly, along with the
remaining orientation ambiguity. The matched lower-bound check abstains.

[Force averages](MATCHED_FORCE_AVERAGE_RESULT.md) · [Full receipt](matched-force-gain-receipt.json).

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.ilvis0_matched_force_gain replay
```
