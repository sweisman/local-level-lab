# The force ordering survived averaging over the same packets

The globe–disc force difference kept its sign in **all 5,946 window, clock
and GPS-stream combinations**, for both the zero and specified background
fields. All 991 supported windows used their original receiver and packet
support. The calculation bounds the whole retained interval under all
allowed timing offsets for the fitted quadratic paths.

| Recorder | Window, clock and GPS combinations | Both shape signs preserved | Largest possible change from a center prediction |
|---|---:|---:|---:|
| IMU8 | 3,648 | 3,648 | 0.0000453 m/s² |
| IMU21 | 2,298 | 2,298 | 0.0000148 m/s² |

The [frozen calculation](MATCHED_FORCE_AVERAGE_PLAN.md) evaluated 23,784
model envelopes using 190,272 interval evaluations. It compares GPS-derived
force predictions over the same times used for the accelerometer bounds.
The ordering describes which shape requires more force on a supplied path.
Deciding which prediction fits the accelerometer requires instrument
calibration and error analysis. The GPS streams share satellite observations,
and the bounds here hold for their fitted paths.

[Window output](matched-force-average-windows.csv.gz) · [Receipt](matched-force-average-receipt.json).

Restore the [prepared inputs](MATCHED_FORCE_SUPPORT_RESULT.md) if they are absent, then replay with

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.ilvis0_matched_force_average replay
```
