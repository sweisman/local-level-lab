# Do two GPS receivers choose the same usable windows?

Eleven pairs of primary GPS receiver recordings cover the same survey legs.
The fixed receiver-only motion screen was applied to both recordings at the
same **490 target times**. This checks whether the screen repeats across
receivers before it is used in a gyroscope/accelerometer comparison. The
twelfth overlapping pair retains its earlier decoder failure and was not
silently repaired.

| Paired result | Target times |
|---|---:|
| Both receivers accept a window | 456 |
| Both reject all windows | 27 |
| One accepts and the other rejects | 7 |

For the 456 times both accepted, they chose the same 5, 10 or 15-second
half-window at **423** times. Across 25,890 exactly matched receiver epochs,
the median pair's vertical-velocity disagreement after removing one constant
pair offset was **0.039 m/s RMS**; the largest pair was **0.122 m/s RMS**.

The [pair table](pairs.csv) shows every pair's counts and velocity differences.
The [target table](targets.csv) retains each common target time, both selected
widths and every candidate rejection reason. The [receipt](receipt.json) binds
both tables to the sealed eleven-pair study, its source and its fixed plan.

The receivers often agree, but they can share satellite and processing errors.
Different antenna positions and aircraft rotation can also create genuine
differences between their reported velocities. This is **relative
repeatability**, not either receiver's absolute velocity accuracy or a
calibrated probability that a selected window is correct. The earlier
[threshold-margin audit](../ilvis0-receiver-support-inventory/MARGIN_AUDIT.md)
shows that some windows lie close to the vertical-motion limit. A later
gyroscope/accelerometer analysis must keep that uncertainty visible.

No IMU increments, fused navigation, physical model fit or protected ESA
recording entered this study. It made no Earth-model decision. All eleven
preselected pair tasks completed and passed; the study charged zero native
model calls.

[Fixed question and execution limits](PLAN.md) ·
[Earlier receiver-position comparison](../ilvis0-receiver-overlap/recorded-study/README.md) ·
[Measurement contribution](../ilvis0-measurement-contribution/README.md).
