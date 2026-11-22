# A broader linear contrast allows 12.18 cm of position error

For the two saved zero-field affine forecasts, the best linear
contrast in the tested representation can tolerate **12.18 cm**
of uniform nonlinear error per coordinate. Two numerical methods
gave the same proposal. The exact lower and upper bounds are
0.1218128769551 m and 0.1218128769651 m, respectively.

| Contrast | Position-error allowance |
| --- | ---: |
| Remove the full calibration span numerically, then verify | 0.48 µm |
| Optimize the allowance and verify both bounds | 12.18 cm |

The broader contrast cancels the original nine smooth terms and
retains every calibration column from both models. It assigns
**46.5%** of its absolute weight to earlier position coordinates.
This freedom is what the broader search permits. The forecast
comparison based on later innovations has more specific weights
on the earlier positions, imposed by the receiver covariance.

This establishes the best margin in the declared affine representation.
It leaves open whether a contrast constrained to the original forecast
conditioning can keep that margin. It also leaves open the full
nonlinear integration bound and aircraft prediction coverage.

The exact checks used both archived parameter boxes, with eight
charged calls and five software checks. No new aircraft fits or
later receiver observations were used.

[Frozen plan](ESA_CALIBRATION_MAXIMUM_MARGIN_PLAN.md) ·
[Verified evidence](esa-calibration-maximum-margin-evidence/README.md)
