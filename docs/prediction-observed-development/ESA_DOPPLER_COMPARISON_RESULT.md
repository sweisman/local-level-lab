# ESA aircraft motion checked directly from Doppler

GPS and GLONASS each yielded a velocity at all **1,041 half-second epochs**.
Over the same two-minute forecast window, the paths obtained by integrating
these velocities stayed within **0.30 m horizontal RMS** and
**0.27 m height RMS** of the original receiver export. Each path starts at
the last earlier receiver position and uses Doppler velocities thereafter.
Neither case applies a later position update or a fitted offset.

| Doppler source | Later velocity difference N / E / Up RMS (cm/s) | Later integrated horizontal / height RMS (m) |
| --- | ---: | ---: |
| GPS | 1.22 / 0.60 / 1.65 | 0.30 / 0.13 |
| GLONASS | 3.48 / 1.30 / 4.90 | 0.22 / 0.27 |

The earlier 399-second integrated paths had 0.71 m horizontal RMS and
1.24 m height RMS for GPS, and 0.52 m and 0.33 m for GLONASS. Over
the later 120 reports the two constellations' velocities differed by
2.96, 1.58 and 3.76 cm/s RMS in north, east and up. The individual
velocity errors were correlated across successive reports. The signed
series and lag correlations are saved with the result.

This checks relative displacement on one flight using two sets of
satellites. Both use the same aircraft antenna, and the starting
position comes from the export. The small displacement differences
leave the absolute position error and aircraft error law open. No
Earth-model fit ran again, and the seven reserved ESA groups stayed closed.

## Reproduce with the sealed local inputs

Use the [GPS](ESA_RINEX_CODE_RESULT.md) and
[GLONASS](ESA_GLONASS_COMPARISON_RESULT.md) position reconstructions,
their sealed raw inputs and the local 800-report receiver study.
Run `freeze` and then `run` for each of these modules, in order,
from the repository root. For example,

```sh
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_doppler_study freeze
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_doppler_study run
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_doppler_comparison freeze
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_doppler_comparison run
```

The controls recover known velocity and clock drift from separately
generated range rates and check integration under exact linear velocity.
Eighteen focused tests passed.

[Velocity plan](ESA_DOPPLER_VELOCITY_PLAN.md) ·
[Comparison plan](ESA_DOPPLER_COMPARISON_PLAN.md) ·
[Signed differences, correlations and hashes](esa-doppler-comparison-result.json)
