# What changes after applying the published GPS antenna corrections?

On the two-minute ESA development comparison, the published satellite and
Nuuk Museum antenna corrections changed the signed aircraft-minus-ground
range score by **0.0012% of the saved model-score gap**. The aircraft-minus-ground
range difference was **8.101 mm RMS** before and after correction at the
displayed precision. The score and its weights came from the original
comparison. The test kept the paths fixed and ran no model fits.

| Correction | Size in the one-second ranges, RMS | Signed change to the aircraft-minus-ground score |
| --- | ---: | ---: |
| Satellite antenna as viewed from the aircraft | 18.12 µm | +0.000000598 |
| Satellite antenna as viewed from Nuuk Museum | 18.45 µm | −0.000000618 |
| Nuuk Museum receiver antenna | 6.27 µm | +0.000000570 |
| Combined | | +0.000000551 |

All 120 intervals and 1,247 matched range values were retained. The
satellite terms largely cancel in this aircraft-minus-ground comparison.
The satellite correction projected onto the full aircraft score, including
the directions missing from the ground match, is +0.000000547.

The replay uses the published IGS20 L1/L2 frequency patterns and the CODE
flight-day attitudes with the saved IGS combined orbit and clock products.
It measures the effect of adding those documented terms under these fixed
products. The aircraft antenna model, reflections near the aircraft,
tracking errors, and carrier phase effects from antenna rotation remain
open. None of the three receiver headers identifies the shared roof
antenna. A separate calculation bounds the effect of tilt for an ideal
antenna. No aircraft error cap was established. The outcome remains abstain.
[Calibration inputs](ESA_ANTEX_INTAKE.md) · [Aircraft antenna inventory](ESA_AIRCRAFT_ANTENNA_INVENTORY.md) · [Ideal antenna tilt bound](ESA_PHASE_WINDUP_RESULT.md) · [Independent evidence required](ESA_NKAR_ERROR_BUDGET_RESULT.md)

Ten qualification tests passed. The completed one-task replay charged all
361 checks, with zero new fits and zero reserved flight reads. A first
attempt stopped on an input-type error. Its receipt, charges and frozen
source remain preserved. [Original plan](ESA_NKAR_ANTENNA_PLAN.md) ·
[Qualified correction](ESA_NKAR_ANTENNA_PLAN_V2.md) · [Sealed result](esa-nkar-antenna-result-v2.json)
