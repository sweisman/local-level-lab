# A one-second carrier test with the distant Qaqortoq receiver

Matching the aircraft and Qaqortoq measurements exposed **98.0% of the signed
carrier weight norm** in the two-minute ESA development score. All 120
one-second intervals passed the continuity and signal checks, with 9–11 GPS
satellites in each. The measured aircraft-minus-ground discrepancy on those
directions was equivalent to **2.46% of the saved score gap**.

| Matched range residual | Signed score equivalent | Share of score gap |
| --- | ---: | ---: |
| Aircraft | +0.001917 | +4.26% |
| Qaqortoq ground receiver | +0.000810 | +1.80% |
| Aircraft minus ground | +0.001107 | +2.46% |

The same fixed weights and final satellite products were used throughout.
The ground receiver gives an independent observation of some common satellite
effects. The station is 456–458 km away. Local atmospheric and antenna errors
can differ, and errors shared by both receivers can cancel in their difference.
Other score directions are outside the matched measurements. The 2.46% result
is a measured discrepancy on the visible part of the score. Absolute aircraft
accuracy and a decision on the independent ESA flights remain open.
[Ground receiver and exact overlap](ESA_QAQ_GROUND_INTAKE_RESULT.md)

The [frozen plan](ESA_QAQ_GROUND_SCORE_PLAN.md) used 121 of 121 charged checks.
Six software tests passed, and the totals were independently recomputed from
the signed rows. No new fits ran and no reserved flight records were read.
The [signed result](esa-qaq-ground-score-result.json) has SHA-256
`98251d43fbaed81aeb24cb3fd8555b74636fab0c1c982a296fb315772e68a185`.

An [earlier-only correction check](ESA_QAQ_PHASE_TRANSFER_RESULT.md) subsequently
found that the distant ground residual made little difference to the later
aircraft RMS or the signed score.
