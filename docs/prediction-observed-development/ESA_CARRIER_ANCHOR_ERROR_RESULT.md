# How accurate must the ground anchors be?

The two-minute ESA comparison can tolerate some position error at all six
reference times, including both endpoints. **If an independent measurement
bounded structured carrier-range error below 1.0 mm RMS**, the calculation
would allow just under **1.01 m per position coordinate** at each anchor, using
the earlier motion limit and the same linearized satellite geometry. At a
1.5 mm range-error cap, the allowable position error falls to 0.49 m.

| Hypothetical cap on structured carrier-range error | Maximum per-coordinate position error at all six anchors |
| ---: | ---: |
| 0 mm RMS | 2.05 m |
| 0.5 mm RMS | 1.53 m |
| 1.0 mm RMS | 1.01 m |
| 1.5 mm RMS | 0.49 m |

The table allows the errors at the six positions to vary independently, with
each error component bounded by the same value. A single small offset shared
by all six positions has about 2,400 times less effect on this score. That
first-order sensitivity does not establish accuracy for large offsets.

The [exact-anchor analysis](ESA_CARRIER_SCORE_BOUND_RESULT.md) gives the
underlying linear range model. The revised bound adds about 0.02193 score units
per metre of allowed coordinate error to the contributions from carrier error
and displacement acceleration. The table uses the previous constructed
displacement's 1.876 mm/s² RMS acceleration as an illustrative cap. Both error
caps require independent evidence. In particular, the residual of the fit to
the aircraft's own carrier data cannot establish that the structured range
error is below a millimetre. The next direct check is a high-rate independent
ground reference on the same flight.

Eleven software tests passed. The [frozen plan](ESA_CARRIER_ANCHOR_ERROR_PLAN.md)
charged 12 of 12 checks and ran zero new fits. No reserved flight records were
read. The [signed result](esa-carrier-anchor-error-result.json) has SHA-256
`173b6541028b1e5db7cc64cec2903788a1b34eb5139d93dfa6e85eb9fdffa1fc`.
