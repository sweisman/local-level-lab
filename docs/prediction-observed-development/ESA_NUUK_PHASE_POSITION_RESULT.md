# The ground correction reduces the north and height adjustments implied by the ranges

The correction learned from earlier Nuuk observations reduced the position
adjustments implied by the later ranges. Over the three 30-second
differences, the peak accumulated height adjustment fell from **21.62 cm**
to **5.19 cm**. The north adjustment fell from **16.65 cm** to **2.93 cm**.
The east adjustment rose from 2.26 cm to 3.73 cm.
[Earlier-to-later range check](ESA_NUUK_PHASE_TRANSFER_RESULT.md)

| Ground treatment | Peak accumulated north adjustment | East | Up |
| --- | ---: | ---: | ---: |
| No correction | 16.65 cm | 2.26 cm | 21.62 cm |
| Full subtraction | 14.48 cm | 5.00 cm | 19.08 cm |
| Earlier multiplier held fixed | 2.93 cm | 3.73 cm | 5.19 cm |

These adjustments come from projecting the signed range residuals onto the
position and clock directions at the saved aircraft path. They accumulate
relative to the first of the four later measurements. They give no absolute
coordinate error estimate. After allowing for the position adjustment and
clock, the earlier multiplier leaves **1.35 cm RMS** range variation.

Height is most sensitive to range errors on these satellite paths. For one
interval, a uniform bound of 1 cm on each satellite range error allows up to
3.07 cm of height error through the linearized position calculation. Applying
the [one-second position target](ESA_GROUND_GRID_SCORE_RESULT.md) will require
the actual 1 Hz overlaps and an error bound for the complete aircraft path.

All four bounded operations completed, and seven focused tests passed. No
trajectory was refitted, and no reserved flight was opened.
[Frozen plan](ESA_NUUK_PHASE_POSITION_PLAN.md) ·
[Verified result](esa-nuuk-phase-position-result.json)
