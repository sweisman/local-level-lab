# The ESA forecast error check depends on the GPS solution

The one steady window that missed the Student error reference with the
original GPS solution fell inside the reference with both alternate
solutions. Several other windows moved below the lower limit. All three
solutions scored the same forecast paths with the same error model.

| GPS position solution | Windows inside the Student reference | Steady window 21856 score |
| --- | ---: | ---: |
| `air1` | 7 of 8 | 491.84 |
| `mosaic03` | 3 of 8 | 370.99 |
| `pwrpak7` | 2 of 8 | 309.58 |

The steady window's reference range is 265.89–482.41. Across all eight
windows, north, east and height RMS differences between an alternate
solution and the original range from 0.18 to 6.38 cm per axis. Even
these differences can change the covariance-weighted error substantially.
The largest score change was 198.77 units. The point-rate and increment
conventions give identical reference outcomes.

Each comparison used 120 matched GPS times. The three solutions share
an antenna and aircraft. This result shows sensitivity to the receiver
solution. Absolute position accuracy and shared satellite or atmospheric
errors remain open. The seven reserved flight groups stay closed.

All eight tasks completed in 4.0 seconds with no errors. They reproduced
the original scores and completed all 32 alternate comparisons across
both input conventions. They used 64 charged calls and zero new trajectory
fits. Seven software checks passed. The first preparation attempt used
forecast-relative times to match GPS timestamps and stopped before any
scoring. The run used the original row indices and verified the absolute
GPS tags and their conversion to the forecast clock.

[Frozen plan](ESA_FORECAST_RECEIVER_TRANSFER_PLAN.md) ·
[Verified evidence](esa-forecast-receiver-transfer-evidence/README.md) ·
[Preparation failure receipt](esa-forecast-receiver-transfer-v1-preparation-failure.json)
