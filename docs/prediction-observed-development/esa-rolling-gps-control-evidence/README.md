# The inertial forecast improved on both GPS rules at three of four cuts

On ESA development recording 187, the inertial forecast had lower
horizontal error than both fixed GPS-only rules after the first three
cuts. After the fourth, holding the last reported GPS velocity fixed
did better than the inertial forecast (**89.85 m versus 144.72 m**).
The inertial forecasts had lower height error at all four cuts.

| Earlier GPS reports | Inertial horizontal / height RMS | Fixed GPS velocity | Fixed GPS turn rate |
| ---: | ---: | ---: | ---: |
| 200 | 0.35 / 0.25 m | 47.07 / 17.70 m | 109.63 / 17.70 m |
| 400 | 5.38 / 0.58 m | 418.42 / 16.88 m | 448.37 / 16.88 m |
| 600 | 28.62 / 0.30 m | 780.76 / 217.12 m | 795.48 / 217.12 m |
| 800 | 144.72 / 4.32 m | 89.85 / 8.56 m | 246.68 / 8.56 m |

Each row compares the same first 120 later receiver reports. Both inertial
error laws agree at the table's precision. The GPS-only rules used earlier
observations and shared the last reported vertical velocity. We reused the
400-report GPS scores and completed six new extrapolations at the other
cuts. Each new forecast was saved before opening its later GPS positions.
The study ran no navigation fits and opened none of the seven reserved
flight groups.

The outcome at the 800-report cut depends on the GPS rule and forecast
horizon. An earlier [comparison over 400 later reports](RECEIVER_REFERENCE_RESULT.md)
used the same training cut. The inertial path had smaller horizontal error
than both GPS-only rules in that comparison, which estimated velocity from
positions. Absolute flight accuracy still needs a separate check. The four
cuts share one flight.

[Frozen plan](ESA_ROLLING_GPS_CONTROL_PLAN.md) ·
[Scores and source receipts](esa-rolling-gps-control.json) ·
[Verified evidence bundle](esa-rolling-gps-control-evidence/replay.zip)
