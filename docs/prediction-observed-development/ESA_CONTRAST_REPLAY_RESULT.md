# Full integration preserves the forecast contrast in four calibration examples

Replacing the affine paths with full integrations changed the contrast
by less than **0.073%** of its certified calibration gap at every checked
point. The two points that meet the original earlier-loss limit changed
the contrast by less than **0.0042% combined**, even if both changes act
against separation.

| Candidate | Earlier loss increase | Meets earlier limit | Largest later position error | Largest later velocity error | Score error as share of gap |
| --- | ---: | :---: | ---: | ---: | ---: |
| Zero-field globe | 0.009885 | Yes | 0.041 mm | 0.013 mm/s | 0.00024% |
| Zero-field disc | 0.009989 | Yes | 0.064 mm | 0.042 mm/s | 0.00394% |
| Zero-field globe | 13.115 | No | 84.93 mm | 0.436 mm/s | 0.0475% |
| Zero-field disc | 19.456 | No | 130.22 mm | 0.613 mm/s | 0.0726% |

In the last two examples, position errors exceed 2.25 cm and change
slowly enough that they have little effect on the contrast. The
observed interval-average velocity errors stay below the
[4.69 mm/s allowance](ESA_INTEGRATED_CONTRAST_SUPPORT_RESULT.md) in all
four examples. These examples do not bound errors elsewhere in the
calibration boxes or validate uncertainty on an independent flight.

Both baselines matched the sealed positions to within one nanometre.
Two tasks completed on two threads in 7.21 seconds, with six native
passes and four bound calls. Five software checks passed. No new
aircraft fits, later GPS positions or reserved observations were used.

[Frozen plan](ESA_CONTRAST_REPLAY_PLAN.md) ·
[Verified evidence](esa-contrast-replay-evidence/README.md)
