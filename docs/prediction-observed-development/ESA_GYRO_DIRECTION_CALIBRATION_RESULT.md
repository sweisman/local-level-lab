# The gyro direction result depends on accelerometer calibration

Subtracting a **+0.10 m/s² constant bias on the accelerometer’s X axis**
reverses the directional ranking in all six settings. This is one
explicit correction inside the original ESA working allowances. It
changes both shapes’ comparison to the same logged observations.
The reversal holds even after allowing either shape any retained
fraction of the specified gyro field.

| Averaging width | Best disc RMS with the X correction | Lower bound on globe RMS with the same correction |
| --- | ---: | ---: |
| 11 reports | 0.149–0.151° | 0.151–0.153° |
| 25 reports | 0.137–0.138° | 0.142–0.144° |

Each row spans the three velocity sources. The X correction is the only
one of 24 signed single-axis endpoints that gives a verified reversal
over the whole retained-fraction range. The total includes gyro bias,
gyro gain, accelerometer bias and accelerometer gain. The nominal
observations still give the globe the smaller directional error.

The force-magnitude check on its own does not exclude the X correction.
After the same earlier constant-offset procedure, its height-adjusted
globe force residual is **0.0038–0.0054 m/s² RMS**, comparable with the
nominal results. We have not established whether that correction agrees
with the earlier position fit or describes the actual instrument.
The direction-only comparison therefore leaves shape unresolved
when the original calibration allowances are admitted.

## What the error bound established

The bound asks how far all allowed corrections could move the measured
angles. By itself it is conservative. It certifies the existing shape
ranking for a gyro bias of about **0.29°/h per axis** with all other
terms fixed. With all four bias and gain terms allowed to change, it
certifies less than 1% of the original common working range. The exact
endpoint replay supplies the reversal that the bound alone cannot prove.

Eight tests passed. The calculation reproduced the nominal angles,
completed all 330 bound evaluations and 25 replays, and used no new
Earth-model fits or reserved group data. Both checks reuse one
development flight. The next gate is to test whether the earlier
position and motion measurements independently constrain the X-axis
accelerometer bias enough for the direction comparison.

## Reproduce with the sealed local inputs

Use the local 400/120 study and the saved matched-field direction
and scalar force results. Run from the repository root.

```sh
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_gyro_direction_calibration freeze
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_gyro_direction_calibration run
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_gyro_calibration_endpoints freeze
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_gyro_calibration_endpoints run
```

[Bound plan](ESA_GYRO_DIRECTION_CALIBRATION_PLAN.md) ·
[Endpoint plan](ESA_GYRO_CALIBRATION_ENDPOINT_PLAN.md) ·
[Exact bounds and hashes](esa-gyro-direction-calibration-result.json) ·
[All endpoint angles and scores](esa-gyro-calibration-endpoints-result.json)
