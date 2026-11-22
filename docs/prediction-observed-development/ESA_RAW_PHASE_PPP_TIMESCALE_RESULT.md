# Longer intervals do not resolve the carrier disagreement

Summing the raw and projected carrier measurements over 4, 16 or
60 seconds did not consistently improve agreement. The comparison
uses the same satellites throughout each block.

| Receiver pair, later portion | 1 s | 4 s | 16 s | 60 s |
| --- | ---: | ---: | ---: | ---: |
| `air1` and `mosaic03` | 1.152 | 1.045 | 1.005 | 0.979 |
| `air1` and `pwrpak7` | 1.039 | 0.939 | 1.000 | 0.966 |
| `mosaic03` and `pwrpak7` | 1.289 | 0.870 | 0.971 | 0.794 |
| Retained blocks | 120 | 30 | 7 | 2 |

The values are squared error divided by squared error from predicting
zero carrier difference. Below one is better. The pair that excludes
`air1` does best at 60 seconds, when only two blocks are available.
The error for pairs containing `air1` still reaches 65–71 mm RMS
over those blocks. In the earlier portion, the two `air1` pairs
improve only at shorter durations and give essentially the same
error as zero at 60 seconds.

The longer comparisons do not support treating raw carrier variation
as a direct estimate of the positioning error. They do not establish
which receiver's position is more accurate. They also provide no
measurement of errors common to all three receivers.

Both tasks finished in 8.0 seconds. The study charged all 687 full
blocks, including those excluded by the original clock break. Five
software checks passed and no aircraft fits or new source reads ran.

[Frozen plan](ESA_RAW_PHASE_PPP_TIMESCALE_PLAN.md) ·
[Verified evidence](esa-raw-phase-ppp-timescale-evidence/README.md)
