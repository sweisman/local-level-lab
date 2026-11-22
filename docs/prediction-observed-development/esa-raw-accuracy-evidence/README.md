# Nine of twelve unadjusted ESA forecasts meet the position-error limits

Both inertial error laws pass on the same **9 of 12** raw forecast windows.
The failures are horizontal and occur at rolling cuts 600 and 800 and at
steady window 21856. The previously released adjustment based on earlier
GPS errors moves that steady window inside the horizontal RMS limit, from
**11.54 m to 0.21 m**. All twelve raw forecasts meet both height limits.

| Turn or steady window | Raw horizontal RMS | Adjusted horizontal RMS | Raw height RMS | Adjusted height RMS |
| --- | ---: | ---: | ---: | ---: |
| Steady 21856 | 11.54 m | 0.21 m | 1.35 m | 0.70 m |
| Steady 32716 | 3.27 m | 0.20 m | 0.25 m | 0.13 m |
| Steady 36436 | 3.04 m | 0.17 m | 0.40 m | 0.05 m |
| Steady 39916 | 0.72 m | 0.22 m | 0.16 m | 0.25 m |
| Turn 22936 | 6.99 m | 0.39 m | 0.11 m | 0.20 m |
| Turn 33796 | 5.86 m | 1.79 m | 0.75 m | 0.83 m |
| Turn 37516 | 1.31 m | 0.35 m | 0.35 m | 0.42 m |
| Turn 41116 | 4.42 m | 1.04 m | 0.90 m | 0.69 m |

The table shows the increment law. Both laws agree on every limit flag.
The adjustment lowers horizontal RMS in all eight windows. Its effect on
height varies. The table and machine-readable result use the same 120 GPS
positions for the raw and adjusted paths. The adjustment in these eight
windows uses residuals from the fit to earlier GPS positions. The separate
[height-error transfer test](ESA_HEIGHT_ERROR_TRANSFER_RESULT.md) used an
earlier forecast's errors and tested a different correction.

The [first accuracy audit](ESA_ABSOLUTE_ACCURACY_RESULT.md) reported 10 of
12 passes by combining four raw rolling forecasts with eight released
adjusted forecasts. The adjustment explains the difference in the counts.
Both audits preserve the original forecasts and require no refits. They
describe one development flight. Independent-flight accuracy and uncertainty
remain open, and the seven reserved flight groups stay closed.

[Frozen plan](ESA_RAW_ACCURACY_PLAN.md) ·
[Both laws and all four limits](esa-raw-accuracy.json) ·
[Verified evidence bundle](esa-raw-accuracy-evidence/replay.zip)
