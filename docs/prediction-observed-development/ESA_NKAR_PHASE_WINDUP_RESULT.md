# Satellite rotation made little difference to the saved range score

The ideal phase correction for moving GPS satellites and upright receiver
antennas changed the aircraft-minus-Nuuk score by **0.000014% of the
original model-score gap**. It changed the full aircraft score by
**0.000194% of that gap**. The aircraft-minus-ground range disagreement
remained **8.101 mm RMS** at the displayed precision.

| Quantity | Result |
| --- | ---: |
| Aircraft phase correction RMS, matched ranges | 4.303 µm |
| Nuuk phase correction RMS, matched ranges | 4.326 µm |
| Aircraft-minus-Nuuk signed score change | +0.00000000642 |
| Full aircraft signed score change | +0.00000008714 |
| Lowest sampled aircraft satellite elevation | 5.0009° |

At the sampled endpoints, maximum aircraft antenna tilt below 5° would
keep every used ray above the plane of the modeled antenna throughout
the change from upright. The [ideal tilt bound](ESA_PHASE_WINDUP_RESULT.md)
would then cap the additional full score shift at about 5.1% of the gap.
The actual tilt, antenna response and shared aircraft range errors
remain unmeasured. This replay supplies no aircraft error cap.

The replay used flight-day CODE satellite attitudes and the same
aircraft path, satellite sets and range weights as the earlier antenna
calibration study. It retained all 240 aircraft pairs, 120 matched
ground pairs and 1,247 matched ranges. Seventeen qualification tests
passed. An independent sum of the saved corrections reproduced both
score changes and the corrected range RMS. The replay charged all
361 checks, with zero model fits and zero reserved flights opened.
[Plan](ESA_NKAR_PHASE_WINDUP_PLAN.md) ·
[Earlier antenna study](ESA_NKAR_ANTENNA_RESULT.md) ·
[Numerical receipt](esa-nkar-phase-windup-result.json)
