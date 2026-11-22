# An earlier Qaqortoq correction makes little difference later

A correction learned from 335 earlier seconds reduced the aircraft range
residual on the later two-minute window from **4.733 to 4.715 mm RMS**.
That is a **0.38% improvement**. The correction shifted the signed carrier
score by **−0.31% of the saved score gap**. Subtracting the full ground
residual increased the later RMS to 5.630 mm.

| Range treatment | Earlier RMS | Later RMS |
| --- | ---: | ---: |
| Aircraft residual | 4.557 mm | 4.733 mm |
| Full ground subtraction | 5.209 mm | 5.630 mm |
| Earlier multiplier, held fixed | 4.524 mm | 4.715 mm |

The earlier multiplier was 0.173. All 335 earlier and 120 later intervals
entered the calculation. They shared no observations and excluded the known
aircraft clock step. The later block had already been used for the fixed
comparison, so this is a chronological check on one development flight.
Qaqortoq is about 456 km away. This result supports keeping its residual as
a check on shared satellite behavior and leaves local error at the aircraft
unbounded. The nearer Nuuk Museum record is still pending.
[Fixed Qaqortoq result](ESA_QAQ_GROUND_SCORE_RESULT.md) ·
[Nuuk data access](ESA_GROUND_REFERENCE_AVAILABILITY.md)

Six software tests passed. The [plan](ESA_QAQ_PHASE_TRANSFER_PLAN.md) closed
with 337 of 337 charged checks, zero model fits and zero reserved-flight
reads. The [result](esa-qaq-phase-transfer-result.json) has SHA-256
`50508c8bc9a6777b44b27533dee56fd977c7874e4a3f1fc46d247f8a2493d61b`.
The multiplier and the later RMS numbers were independently reproduced from
the signed rows in the two reports.
