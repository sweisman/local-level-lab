# Direct Doppler motion at the Reykjavík stop

The path obtained by integrating the aircraft receiver's direct GPS
Doppler velocities ended **21.72 m down** after 30 minutes. The original
GPS position solution ended **0.01 m down**. The fixed-station carrier-phase
comparison ended **0.99 m up**. All three paths start at zero displacement.
Direct Doppler drift is too large here to resolve the sub-metre difference
between the two position paths.

| Reference for the Doppler path | Position difference N / E / up RMS (m) | Difference in 30-second displacements N / E / up RMS (m) |
| --- | ---: | ---: |
| Aircraft GPS position solution | 6.27 / 2.05 / 14.61 | 0.178 / 0.094 / 0.396 |
| Relative carrier phase against the station | 6.53 / 2.37 / 15.42 | 0.183 / 0.100 / 0.415 |

The fixed-station control itself shows apparent velocity of **1.55, 1.26
and 2.76 cm/s RMS** north, east and up. Those measurements come 30 seconds
apart and cannot supply a correction for every half-second aircraft epoch.
The aircraft path uses no fitted trend, position update or station
correction. This check measures the disagreement among methods during
one ground stop. Its measurement uncertainty does not transfer to flight.

Both tasks completed within the [frozen allowance](ESA_FIXED_REFERENCE_DOPPLER_STAGED.md).
The saved series include 3,601 aircraft estimates and 61 station estimates.
Each uses eight to ten of the ten GPS satellites originally chosen for the
carrier-phase comparison. The two series were sealed separately before
integrating the aircraft velocities and comparing the 61 shared times.
The [earlier execution failures](ESA_FIXED_REFERENCE_DOPPLER_STATUS.md)
are preserved. No aircraft inertial fit or reserved-flight read occurred.

From the repository root with the sealed local study available, regenerate
the comparison from saved velocities without rerunning any solve:

```sh
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_fixed_reference_doppler report
```

[Displacements and evidence hashes](esa-fixed-reference-doppler-result.json) ·
[Carrier-phase and clock replay](ESA_FIXED_REFERENCE_CLOCK_RESULT.md)
