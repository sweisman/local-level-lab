# Final GPS orbits preserve the ESA forecast ranking

Replacing broadcast satellite positions with the IGS final orbits shifted
the GPS solution by **0.90 m RMS** over the 120 later positions
used to score the forecasts. The horizontal and height shifts were
**0.54 m** and **0.72 m RMS**. All three forecasts kept the same rank, and
the specified-field globe continued to pass the fixed position limits.

| Satellite orbit product | Specified-field globe | Zero-field globe | Stationary disc |
| --- | ---: | ---: | ---: |
| Broadcast | 6.74 m | 2,590.01 m | 3,998.63 m |
| IGS final | 6.49 m | 2,589.59 m | 3,998.18 m |

The table shows total position RMS for the increment error convention.
The point convention gave the same ranking and preferred-model accuracy
result. Both comparisons use the same 120 match times and the existing
forecasts. All original broadcast scores reproduced before the final
orbit table was checked.

The receiver replay completed **1,041 of 1,041 epochs** in **23 seconds**.
Each epoch kept its original satellite set, transmit times, broadcast
clocks and dual-frequency code. The largest change in a satellite's
calculated position was **2.69 m**. The median range residual changed
from **1.70 m to 1.74 m**. The new orbit positions were used with the
same broadcast clocks, so the larger residual only describes this
combined calculation.

This test isolates one error that all three airborne receivers could
share. Absolute position accuracy and errors shared across other parts
of the receiver solution remain open. A [separate clock test](ESA_RELATIVE_CLOCK_REPLAY_RESULT.md)
uses the same reduced satellite set in both arms because the final clock
product omits G17. The orbit test reused saved forecasts, made zero inertial
fits and kept the protected flights sealed.
[Orbit and clock coverage](ESA_PRECISE_GPS_SUPPORT_RESULT.md)

## Reproduce the tables

The replay uses the sealed AIR1 excerpt and broadcast navigation product,
the saved code-position rows and the final orbit file. The scoring step
also needs the sealed 400/120 forecast study and the earlier paired
GPS score files. The linked result records the signed position changes,
scores and hashes. The original receiver positions and forecast artifacts
remain in their study stores.

For a new reproduction directory with the frozen inputs, prepare the
study and run the nine blocks. For a verified completed directory, run
only the scoring command.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_final_orbit_replay prepare
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.studies run \
  data/esa-final-orbit-replay-v2 --reserved-threads 0
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_final_orbit_score
```

[Fixed method](ESA_FINAL_ORBIT_REPLAY_PLAN.md) ·
[First launch and accounting correction](ESA_FINAL_ORBIT_REPLAY_ACCOUNTING.md) ·
[Saved effects and scores](esa-final-orbit-score-result.json)
