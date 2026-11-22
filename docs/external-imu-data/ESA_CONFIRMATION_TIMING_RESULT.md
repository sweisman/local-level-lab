# Sample timing in the seven reserved ESA groups

**All seven selected 20-minute slices passed the timestamp check.** The
earliest provisional GPS window in each reserved group supplied one slice.
The IMU records bracketed the two endpoints of each slice. Across 2,519,980
in-slice records, every adjacent interval that touched a slice was between
3.333 and 3.334 ms. The gap limit was 5 ms. The longest provisional GPS
windows extend beyond this check. [Receiver screening](ESA_CONFIRMATION_RECEIVER_INVENTORY_RESULT.md)

The check used line framing and the printed GPS time field. The sensor
columns were not decoded. Prediction quality, calibration and the aircraft
error law still need qualification before confirmation. No Earth-model fits
or model outcomes entered this check.

All seven transfers produced the exact byte counts required by the frozen
range plan. Five transfers reported an FTP control-response timeout after
delivering those bytes. The worker verified the framing, time coverage and
SHA-256 of every received range. The original excerpts remain in local
storage. [Plan](ESA_CONFIRMATION_TIMING_PLAN.md)

The [verified timing results](esa-confirmation-timing-v1-result.json) have
SHA-256 `ec7e5433620d7d08da6f5995126b3d7792ebc5d9bc267c6907dd78b27e96d79c`.
All 40 focused tests passed. The closed study can reproduce this report
without retrieving the original samples. [Evidence package](esa-confirmation-timing-v1-evidence/README.md)

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_confirmation_timing report
```
