# The archived carrier signature survives at one-second spacing

Summing the saved half-second aircraft changes preserves the constructed
motion signature at the Nuuk receiver's cadence. Hiding that motion would
require a **9.77 mm RMS** correction to the satellite ranges over each
second, nearly identical in rate to the original half-second comparison.
The archived satellite clock update still has little alignment with the
required correction. [Original comparison](ESA_SHARED_MOTION_CARRIER_RESULT.md)

| Quantity | RMS over one second |
| --- | ---: |
| Required correction to hide the constructed motion | 9.77 mm |
| Archived satellite clock correction | 1.17 mm |
| Required correction minus archived correction | 9.89 mm |

The replay used 120 consecutive GPS seconds and 1,247 satellite comparisons,
with 9–11 satellites common to both half-second records in each pair. It
removed one common clock term per pair. The archived correction contributed
−0.51% of the required pattern in the signed projection. The numbers come from
sums of the saved half-second models. Direct evaluation of the one-second
endpoints could choose different broadcast ephemerides.

The calculation gives a signal scale for the future ground comparison.
Actual satellite overlap, phase continuity and correlated range errors
remain to be checked on the ground file. There were no new fits or ground
or reserved flight reads. Eleven focused software checks passed.
[Frozen plan](ESA_NKAR_CADENCE_PLAN.md) ·
[Verified result and signed sums](esa-nkar-cadence-result.json) ·
[Evidence receipt](esa-nkar-cadence-evidence/evidence-receipt.json) ·
[Ground file availability](ESA_GROUND_REFERENCE_AVAILABILITY.md)
