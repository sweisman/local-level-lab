# A fixed quartz alignment fails to carry across the development flight

An alignment learned from the first 240 seconds left **17.2–18.4
mm/s² RMS** of northward disagreement on the following 144 seconds.
That is about nine times the 1.894 mm/s² position-acceleration scale
of the north–south path error that could span the carrier score gap.
The two quantities have different time averaging. Their sizes show
why this alignment supplies no useful motion bound for that path test.
[North–south sensitivity](ESA_MOTION_AXIS_SUPPORT_RESULT.md)

| Zero-field geometry used for the GPS force calculation | First 240 s vector RMS | Next 144 s vector RMS with earlier alignment | Next 144 s north RMS | Next 144 s vector RMS after fitting those same data |
| --- | ---: | ---: | ---: | ---: |
| Globe | 85.21 | 27.97 | 17.20 | 1.18 |
| Disc | 86.92 | 29.81 | 18.41 | 1.25 |

All errors are in mm/s². Both earlier fits choose +0.1 seconds, the edge
of the tested clock grid. Both internal refits retain the same axis
handedness and change the fitted orientation by about 28–29°. This
change can absorb differences in time, platform motion or force response.
The small error after refitting the check intervals leaves the earlier
alignment unqualified.

The sixteen fixed 24-second supports are entirely within the original
earlier receiver interval. The sealed result retains all clock alternatives,
the saved selection and the six signed check residuals for each geometry.
An independent calculation reproduced the reported errors. Thirteen
software checks passed and all 17 charged operations completed. Zero
Earth-model fits ran and no reserved flights were opened.
[Frozen plan](ESA_GIRAFE_DIRECTION_TRANSFER_PLAN.md) ·
[Saved results](esa-girafe-direction-transfer-result.json)
