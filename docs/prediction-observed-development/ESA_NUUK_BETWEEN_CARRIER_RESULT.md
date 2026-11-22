# The half-second carrier records constrain the between-sample displacement

The position error that vanishes at the four Nuuk ground times still changes
the aircraft-only carrier residual. The RMS residual rises from **3.77 mm**
on the saved path to **4.74 mm** on the displaced path. It rises on all 240
half-second pairs. [Constructed displacement](ESA_NUUK_BETWEEN_SAMPLES_RESULT.md)

| Half-second comparison | RMS across satellite ranges |
| --- | ---: |
| Signed range correction needed to hide the displacement, all used satellites | 2.88 mm |
| Required correction on the archived clock subset | 3.01 mm |
| Archived satellite clock change on that subset | 0.58 mm |
| Difference between required correction and clock change | 3.07 mm |

The signed archived clock change contributes −0.09% of the required pattern's
amplitude. That update alone cannot hide this displacement. The tested
displacement, satellite navigation, transmit times and atmospheric correction
were fixed. The comparison uses 2,736 range values, including 2,496 with an
archived final clock correction.

The aircraft-only path was estimated from the same observations. Its smaller
residual documents the cost of this displacement under that range model.
The measurements still permit a coherent error of unknown size that affects
both the path solution and the residual. The 30-second ground samples miss
the constructed position change. The 1 Hz reference would check more of the
intervening motion. [Ground reference](ESA_GROUND_REFERENCE_AVAILABILITY.md)

Fourteen focused tests passed. The study completed all 241 bounded operations
and used no new position or inertial fits and no reserved recordings.
[Frozen plan](ESA_NUUK_BETWEEN_CARRIER_PLAN.md) ·
[Verified result and signed differences](esa-nuuk-between-carrier-result.json)
