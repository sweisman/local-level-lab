# Matching accelerometer packets to the GPS windows

All **991 eligible 30-second windows** retained about 5,940 whole packets on
both clocks under the full ±0.15-second offset. The 680 training and 311
later windows stay on their own sides of the prediction cut. The inventory
also keeps 60 windows crossing the cut and 61 without GPS support.

The table reports medians in m/s². The count width is the full interval for
the magnitude of the integrated packets under a half-count error on each
axis. The clock shift uses the very same packets with different durations.
The GPS shape gaps compare globe and disc using the same specified field
or zero field at the center of each window.

| Recorder | Count interval width | Absolute clock shift | GPS shape gap, zero field | GPS shape gap, specified field |
|---|---:|---:|---:|---:|
| IMU8 | 0.01275 | 0.000625 | 0.01012 | 0.05623 |
| IMU21 | 0.0000299 | 0.000185 | 0.00819 | 0.00548 |

On this IMU8 recording, the count interval is of the same order as the
zero-field GPS shape gap. For IMU21 the interval is much smaller than the
gaps. These are scale comparisons. The recorded packet average and the
GPS prediction at a window's center describe different time support.
The next calculation must average each model's force over the retained
packet intervals and carry receiver and calibration uncertainty through it.

The audit used only saved accelerometer counts, timestamps and GPS window
metadata. It applied no attitude-rate limit and established no upper bound
on continuous force. It started no fits and made no model decision.

[Frozen plan](MATCHED_FORCE_SUPPORT_PLAN.md) · [Window table](matched-force-support-windows.csv.gz) ·
[Verification receipt](matched-force-support-receipt.json).

If the prepared inputs are absent, restore the eight files from the shared
archive before replaying the calculation.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies restore data/ilvis0-matched-observed-inputs-v1-20261118
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.ilvis0_matched_force_support replay
```
