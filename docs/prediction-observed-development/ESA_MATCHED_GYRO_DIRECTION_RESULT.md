# The measured force directions distinguish shape under a matched field

Giving the disc the same specified local background field narrows
the difference, but the globe still follows the gyro-derived angles
more closely. This holds in all six receiver and averaging combinations,
even when each shape gets its own retained gyro fraction anywhere
from zero to one.

| Averaging width | Best tested globe RMS | Best tested disc RMS | Minimum advantage over any disc fraction |
| --- | ---: | ---: | ---: |
| 11 reports | 0.008–0.011° | 0.088–0.090° | 0.066–0.071° |
| 25 reports | 0.002–0.003° | 0.076–0.077° | 0.062° |

Each range runs over the exported, GPS Doppler and GLONASS Doppler
velocity sources. Both shapes did best at full retention on the tested
grid. The minimum advantage allows for all fractions between the tested
values. It comes from a bound on how fast the predicted angles can change
as the retained fraction varies.

The disc's field is defined along the recorded route. Both candidates
use the same specified local field in the force equations. The fraction
changes only which frame the logged gyroscope is assumed to describe.
This check covers that family of field-removal assumptions and keeps
gyro bias, gain, gravity and the force observations fixed.

The result puts a scale on the remaining calibration question. The
comparison survives an RMS change of **0.0309°** to the eight
measured angles in the least separated setting, with the predicted
angles fixed. No calibration check has yet established that bound on
the actual measurement and processing errors. All comparisons reuse
the same already opened flight and the same earlier 400 reports.

The two endpoints reproduce the earlier globe calculation. Nine
focused tests passed. No inertial samples were reread, no new fit ran,
and the seven reserved ESA groups stayed closed.

## Reproduce with the sealed local inputs

Use the [prior gyro direction result](ESA_GYRO_FORCE_DIRECTION_RESULT.md)
and the same local Doppler and 400/120 artifacts. Run from the repository
root.

```sh
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_matched_gyro_direction freeze
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_matched_gyro_direction run
```

[Frozen plan](ESA_MATCHED_GYRO_DIRECTION_PLAN.md) ·
[Profiles, error bounds and hashes](esa-matched-gyro-direction-result.json)
