# Ten of twelve ESA development windows meet the position-error limits

Both inertial error laws pass on the same **10 of 12** windows. All four
turn windows and all four steady windows pass. Two rolling cuts miss the
10 m horizontal RMS limit. The cut after 800 reports also exceeds the
50 m peak horizontal limit. All twelve meet both height limits.

| Window | Horizontal RMS | Peak horizontal | Height RMS | Peak absolute height | Limits met |
| --- | ---: | ---: | ---: | ---: | --- |
| Rolling cut 200 | 0.35 m | 0.98 m | 0.25 m | 0.56 m | All |
| Rolling cut 400 | 5.38 m | 7.66 m | 0.58 m | 0.76 m | All |
| Rolling cut 600 | 28.62 m | 37.44 m | 0.30 m | 0.54 m | Height and peak horizontal |
| Rolling cut 800 | 144.72 m | 176.48 m | 4.32 m | 4.51 m | Height |
| Steady 21856 | 0.21 m | 0.50 m | 0.70 m | 1.39 m | All |
| Steady 32716 | 0.20 m | 0.47 m | 0.13 m | 0.28 m | All |
| Steady 36436 | 0.17 m | 0.45 m | 0.05 m | 0.14 m | All |
| Steady 39916 | 0.22 m | 0.48 m | 0.25 m | 0.53 m | All |
| Turn 22936 | 0.39 m | 0.94 m | 0.20 m | 0.34 m | All |
| Turn 33796 | 1.79 m | 4.72 m | 0.83 m | 1.79 m | All |
| Turn 37516 | 0.35 m | 1.19 m | 0.42 m | 0.91 m | All |
| Turn 41116 | 1.04 m | 3.17 m | 0.69 m | 1.44 m | All |

Each row uses the larger value across the two laws for each column. The
audit used exactly 120 later GPS positions per window and applied the
existing limits of 10 m horizontal RMS, 50 m peak horizontal error,
30 m height RMS and 150 m peak absolute height error. For the turn and
steady windows, it first reproduced their reported RMS values in the
original local frame, then used the same GPS-position scale as the
rolling cuts. No navigation fits were run.

All windows come from development recording 187. The results show where
the saved forecasts meet a fixed descriptive accuracy check. The sample
provides no independent-flight success rate. The seven reserved flight
groups remain closed.

[Frozen plan](ESA_ABSOLUTE_ACCURACY_PLAN.md) ·
[All scores and checks](esa-absolute-accuracy.json) ·
[Verified evidence bundle](esa-absolute-accuracy-evidence/replay.zip)
