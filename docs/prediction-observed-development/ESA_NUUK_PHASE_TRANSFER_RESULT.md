# An earlier Nuuk correction improves later range agreement

A correction learned from the first part of the development flight lowered
the later aircraft carrier residual from **4.38 cm to 1.92 cm RMS**. It helped
on each of the three later 30-second intervals. Subtracting the entire ground
residual gave 3.58 cm RMS. [Frozen plan](ESA_NUUK_PHASE_TRANSFER_PLAN.md)

| Later range residual | No ground correction | Full ground subtraction | Earlier multiplier held fixed |
| --- | ---: | ---: | ---: |
| Ionosphere-free combination | 4.38 cm | 3.58 cm | 1.92 cm |
| L1 band | 6.83 cm | 4.62 cm | 3.65 cm |
| L2 band | 9.24 cm | 6.64 cm | 5.83 cm |

The multiplier was 0.581 for the combined bands. It was estimated from 11
earlier intervals. The three later intervals shared no epochs with those
used for estimation. The interval containing the known aircraft clock step
and the transition into the later group were left out. There were no broadcast
ephemeris changes on the selected arcs. The aircraft path stayed fixed for
every comparison.

The later improvement shows that a nearby ground receiver can help account
for some of the range variation seen aboard the development flight. The
numbers describe range residuals on one saved path. They leave the absolute
aircraft coordinate error and the errors between ground samples unbounded.
The [one-second position benchmark](ESA_GROUND_GRID_SCORE_RESULT.md) still
needs measurements at that cadence.
The [position projection](ESA_NUUK_PHASE_POSITION_RESULT.md) finds that this
earlier multiplier reduces the north and height adjustments implied by the
later ranges and increases the east adjustment.

The study completed all 19 bounded operations. Eight focused tests passed.
No receiver position or inertial model was refitted. No reserved recording
was opened. [Verified result](esa-nuuk-phase-transfer-result.json)
