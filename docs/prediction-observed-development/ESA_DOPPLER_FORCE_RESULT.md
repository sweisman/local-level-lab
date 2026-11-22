# What the accelerometer alone resolves on the ESA development cut

The shape difference is smaller than the receiver and accelerometer
disagreements on this cut. The comparison uses the same time weights
on the logged iMAR acceleration magnitude and on the force each model
requires. It uses no gyroscope or fused attitude.

| Quantity across the fixed settings | RMS (m/s²) |
| --- | ---: |
| Globe–disc contrast at the same background field, after an early offset | 0.000042–0.000058 |
| Globe–disc contrast at zero field, after an early offset | 0.000049–0.000072 |
| Change in specified-field globe force when the velocity source changes | 0.000097–0.001765 |
| Difference between logged force and the specified-field globe, after an early offset | 0.00382–0.00731 |

The absolute matched-field shape contrast was about 0.00069 m/s².
Most of it was nearly constant across the cut, so it could be
absorbed by the offset. The remaining contrast is smaller than the
effect of switching among exported velocity, GPS Doppler and
GLONASS Doppler. Eleven of the twelve settings gave the
specified-field globe the smallest numerical error. The other gave
the matched-field disc a smaller error by just 0.0000034 m/s².
Those near ties leave the accelerometer-only shape comparison
unresolved. They should not be counted as independent votes.

The three velocity sources, two stencil widths and two gravity
choices were fixed before the comparison. The first eight blocks
supplied the offsets and the next eight supplied the scores. All
16 blocks are inside the earlier 400 reports of the original study.
The iMAR magnitude comes from the sealed velocity increments divided
by their clock intervals. No original dataset file was reopened, no
new Earth-model fit ran, and the seven reserved groups stayed closed.

The full inertial forecasts separate the models much more strongly
on this flight. This comparison narrows the explanation by showing
that this specific force-magnitude control cannot recover that
separation. It leaves the size of the gyroscope's unique contribution
and the absolute aircraft error law unqualified.

Three focused tests check the time kernel, coordinate-rate conversion
and required force for a stationary path. Six related tests passed.
The saved result includes all force values and the exact freeze. Use
the sealed Doppler and original 400/120 study artifacts, then reproduce
from the repository root.

```sh
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_doppler_force freeze
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_doppler_force run
```

[Frozen plan](ESA_DOPPLER_FORCE_PLAN.md) ·
[Force values, offsets and hashes](esa-doppler-force-result.json) ·
[Full inertial forecast comparison](ESA_400_120_MODEL_MATRIX_RESULT.md)
