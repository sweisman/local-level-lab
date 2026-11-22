# A calibration-resistant contrast leaves a submicrometre error budget

Removing the effects of both calibration spans leaves a positive
gap in the saved affine forecast approximation. Its allowed
nonlinear position error is only **0.48 micrometres per coordinate**.
The available integration bounds do not support such a small error.

| Numerical proposal | Nominal score | Lower gap over both calibration boxes | Uniform position error allowance |
| --- | ---: | ---: | ---: |
| Remove nine smooth terms only | 25.4135 | −661.8087 | None |
| Also remove half the calibration span | 0.011835 | −0.046865 | None |
| Also remove the full calibration span | 0.000719 | +0.000405 | 0.48 µm |

All three proposals were then checked in rational arithmetic. Each
score cancels constants, linear trends and quadratic trends exactly
on all three axes. The bound retains all 51 calibration columns from
each forecast, including the small effects left by numerical
projection. The full-span numerical construction uses 102 directions.

This verifies a separation only in the saved affine approximation
and its calibration boxes. It does not resolve the nonlinear shape
comparison or justify a statistical decision on the aircraft. The
calculation used seven charged calls and two software checks, with
zero new fits or later receiver observations.

[Frozen plan](ESA_CALIBRATION_ORTHOGONAL_PLAN.md) ·
[Verified evidence](esa-calibration-orthogonal-evidence/README.md)
