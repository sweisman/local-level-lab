# The Nuuk ground receiver does not show the error pattern needed to hide the test displacement

The measured range changes from the aircraft and permanent Nuuk receivers
agreed with the saved aircraft path to **3.55 cm RMS**. Adding the constructed
displacement increased the difference to **18.90 cm RMS**. The displaced path
gave a larger discrepancy in each of the three 30-second intervals and after
omitting any one of the eleven satellites. [Verified overlap](ESA_NUUK_GROUND_INTAKE_RESULT.md) ·
[Constructed displacement](ESA_SHARED_MOTION_GAP_RESULT.md)

| 30-second range comparison | RMS across 33 satellite values |
| --- | ---: |
| Correction needed to hide the constructed displacement | 17.89 cm |
| Ground receiver residual | 6.96 cm |
| Required correction minus measured ground residual | 19.87 cm |
| Aircraft minus ground residual, saved path | 3.55 cm |
| Aircraft minus ground residual, displaced path | 18.90 cm |

The signed projection of the ground residual onto the required pattern
was −4.12%. Omitting one satellite at a time gave −6.61% to −1.05%. The
ground receiver residual pointed slightly away from the required correction.
There were no broadcast ephemeris changes on the selected arcs. Across the
same three differences, the individual ground L1 and L2 residuals were 8.71
and 10.50 cm RMS before combining the two bands to remove the leading
ionospheric effect.

The result tests one displacement on 90 seconds of one development flight.
It reduces the plausibility of a shared range error with that particular
pattern. Errors at the aircraft antenna and changes between ground samples
remain open. The calculation uses an approximate fixed station coordinate
and the existing atmospheric model. It gives no calibrated bound for the
full flight. A higher-rate reference could cover the complete two-minute
example and resolve faster changes. [Nuuk Museum reference](ESA_GROUND_REFERENCE_AVAILABILITY.md)

The first worker stopped at the accounting check before it read any
observations. The corrected task verified the same input bytes and
completed all eight declared operations. Twelve software tests passed.
The result stores the signed differences, model geometry, omissions and
completion hashes. No new fits or reserved flights entered the comparison.
[Scientific plan](ESA_NUUK_GROUND_PHASE_PLAN.md) ·
[Accounting and retained failure](ESA_NUUK_GROUND_PHASE_PLAN_V2.md) ·
[Verified result](esa-nuuk-ground-phase-result.json) ·
[AirQuantumGrav data source](https://doi.org/10.57780/esa-58c58c5) ·
[SONEL ground data](https://www.sonel.org/Data-access)
