# The 30-second ground samples leave room for a smaller displacement

A constructed position error can span the same fixed score gap while
vanishing at all four permanent Nuuk comparison times. Its minimum RMS
acceleration is **1.876 mm/s²**, about **14%** above the earlier example.
The largest displacement at the calculation knots is **17.4 cm**.
[Frozen plan](ESA_NUUK_BETWEEN_SAMPLES_PLAN.md) ·
[Earlier example](ESA_SHARED_MOTION_GAP_RESULT.md)

| Position conditions | Minimum RMS acceleration | Largest displacement at a knot |
| --- | ---: | ---: |
| Close the two-minute window in position and velocity | 1.649 mm/s² | 72.4 cm |
| Also return to the saved position at all four ground times | 1.876 mm/s² | 17.4 cm |

The second path puts more of its displacement between the ground samples.
Exact integration verified every anchor, zero endpoint velocity and the
same change in the saved score. This quantifies what the four timestamps
alone can constrain. The subsequent [aircraft carrier replay](ESA_NUUK_BETWEEN_CARRIER_RESULT.md)
finds that this displacement raises the half-second range residual from
3.77 to 4.74 mm RMS. The higher-rate ground observations would check more
of the gaps and help bound errors shared by the aircraft solutions.
[Measured 30-second comparison](ESA_NUUK_GROUND_PHASE_RESULT.md) ·
[One-second reference availability](ESA_GROUND_REFERENCE_AVAILABILITY.md)

Eight focused tests passed. The study completed both bounded operations
and saved the full error path and completion hashes. It used no new fits
or reserved flights. [Verified result](esa-nuuk-between-samples-result.json)
