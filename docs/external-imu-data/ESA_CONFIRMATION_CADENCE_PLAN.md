# Check the development forecast cadence on the reserved windows

Development forecasting used [every other report](../analysis-provenance/esa-forecast-cuts.csv)
from the 2 Hz GPS receiver export. The [first time-window check](ESA_CONFIRMATION_QUERY_RESULT.md)
used every report. Keeping the same number of reports at the original
development cadence approximately doubles the time covered.

For each of the seven previously checked 20-minute slices, take the first
1,840 consecutive source records after the first second. Keep every second
record, beginning with the second one, as in the development stride.
Keep at least one second of IMU timing support after the last query.
Require one GPS week and every original receiver gap at most 0.75 seconds.

The last 400 of the first 800 retained query times supply the shorter
training layout. The longer layout uses all 800 training times. Both use
the same next 120 times for later receiver scoring. Record exact indices,
time-list hashes and observed gaps. Leave the choice of interval and
training length to the final confirmation protocol.

Check the hash of each complete original receiver file. Decode only the
receiver sequence number, GPS week and time. Do not open the sensor columns
of the reserved IMU files or any receiver coordinates for this check.
Allow at most seven declared receiver files, no model fits, and no
substitute slices if one fails.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_confirmation_cadence freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_confirmation_cadence check
```
