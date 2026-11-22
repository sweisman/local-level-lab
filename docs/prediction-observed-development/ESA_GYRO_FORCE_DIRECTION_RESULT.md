# The gyroscope resolves changes in force direction

On the opened ESA development cut, the specified-field globe gives
the closest match to the measured direction changes in all six
receiver and averaging combinations when the logged gyro retains
the field. Its angular error is **0.002–0.011° RMS**. The still globe
and stationary disc have substantially larger errors.

| Candidate and gyro recording assumption | 11-report averages, RMS | 25-report averages, RMS |
| --- | ---: | ---: |
| Specified-field globe, field retained | 0.008–0.011° | 0.002–0.003° |
| Specified-field globe, field fully removed | 0.186–0.190° | 0.174–0.176° |
| Still globe | 0.186–0.190° | 0.173–0.174° |
| Stationary disc | 0.264–0.269° | 0.229–0.230° |

Each range covers the exported, GPS Doppler and GLONASS Doppler
velocity sources. The gyro expresses the logged force vectors in a
single starting frame. The test compares the angles between the
vectors, so a common unknown starting attitude cancels. Each score
uses eight preregistered pairs spaced about 200 seconds apart. The
different pairs reuse parts of the same gyroscope path.

The earlier force-magnitude check left shape unresolved. This
directional check shows what changes when the logged gyro is used.
It does not isolate shape under arbitrary background fields or
calibration corrections. Gyro bias, gain and any partial onboard
field removal have not been bounded by this test. The result is a
descriptive comparison on one already opened flight.

The check uses 119,865 sealed gyro intervals and all 16 fixed earlier
centers. It uses no fused attitude, later 120 receiver records,
original data-file reads, or new fits. The seven reserved groups
remained closed. Six related tests passed, including known
noncommuting rotations and frame-invariant angles.

## Reproduce with the sealed local inputs

Use the [Doppler reconstruction](ESA_DOPPLER_COMPARISON_RESULT.md) and
the local sealed 400/120 study. Run from the repository root.

```sh
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_gyro_force_direction freeze
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_gyro_force_direction run
```

[Frozen plan](ESA_GYRO_FORCE_DIRECTION_PLAN.md) ·
[Individual angles and hashes](esa-gyro-force-direction-result.json)
