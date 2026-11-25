# Verify the seven RF04 checks

All seven checks trace back to the same IceBridge flight stretch. They use
443 one-second reports from NCAR and the matching Applanix record. The
later force and acceleration comparisons retain the same 265 earlier and
118 later centers. These are repeated checks on one recording, so their
windows and outcomes should never be counted as independent flights.
[Source and timing](../ilvis0-measurement-contribution/NCAR_RF04_INTAKE.md)

| Check | What it verifies |
| --- | --- |
| [Whole-second motion](../ilvis0-measurement-contribution/RF04_MOTION_MATCH_RESULT.md) | Compares attitude changes and GPS context between the two recorders. |
| [Receiver offset](../ilvis0-measurement-contribution/RF04_RECEIVER_OFFSET_RESULT.md) | Tests a delay-like offset using earlier positions and checks it on later positions. |
| [Single-packet force directions](../ilvis0-measurement-contribution/RF04_FORCE_DIRECTION_RESULT.md) | Uses separate RF04 attitude to compare predicted and measured force directions. |
| [Averaged force directions](../ilvis0-measurement-contribution/RF04_FORCE_AVERAGE_RESULT.md) | Scores both packet clocks on identical later centers at two averaging widths. |
| [Receiver acceleration](../ilvis0-measurement-contribution/RF04_REFERENCE_ACCELERATION_RESULT.md) | Compares horizontal acceleration derived from positions with changes in reported velocity. |
| [Velocity reporting](../ilvis0-measurement-contribution/RF04_VELOCITY_RESOLUTION_RESULT.md) | Tests whether a plausible rounding scenario could cover the eastward differences. |
| [Antenna motion](../ilvis0-measurement-contribution/RF04_ANTENNA_MOTION_RESULT.md) | Tests if rounding and fixed antenna separation could account for the remaining northward differences. |

From the repository root, verify the seven result reports, frozen sources
and inputs, and all 183 recorded operations. The check verifies the
original Applanix bytes in the archive and links the NCAR extracts to
their recorded netCDF hash. It runs entirely from the repository and its
evidence packs. Recreating the NCAR extracts from the flight netCDF is a
separate step described in the intake guide.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.rf04_evidence
```

The verification checked 2,377 receipt members, including 2,211 frozen
source entries and 73 input entries. These counts include files reused
across studies.

The checks establish what the supplied reports can support. Faster aircraft
motion, the actual antenna separation and the absolute receiver error remain
unresolved. No Earth-model fit starts or reserved ESA observations were used.
