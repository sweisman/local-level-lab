# The ESA forecast gaps after accounting for correlated errors

On development recording 187, accounting for correlation with the 400
earlier receiver positions reduced the gaps between the three predicted
paths from kilometres to tens of metres. Each complete covariance
reproduced the original earlier weights exactly. The comparison used
the three earlier-only fits and the original recorded inertial motion
through the 120 later forecast times.

| Pair | Conditioned separation, RMS | Maximum affine closure at the 0.01 loss allowance |
|---|---:|---:|
| Specified-field globe and zero-field globe | 38.85 m | 0.367 m |
| Specified-field globe and zero-field disc | 62.40 m | 0.356 m |
| Zero-field globe and zero-field disc | 24.30 m | 0.238 m |

The closure bounds use all 27 calibration parameters, the original
parameter limits and the same local box as the
[raw forecast comparison](ESA_CALIBRATION_CONTRAST_RESULT.md).
Under the fixed error laws and affine approximation, at least 99% of
each nominal gap remains along the direction joining the paths.
The loss allowance is a diagnostic scale with uncalibrated coverage.

Exact propagation of the selected steps gave later movements within
0.04 mm of their affine estimates. Eight of the 12 original steps
were within the earlier loss allowance. All 12 were within it at 98%
of their original size. These checks verify the particular finite
steps. An aircraft decision still needs a bound over the full nonlinear
region and independent evidence for the change in error across the
training cut.

Both runs passed all three technical tasks. No fits were repeated and no
withheld receiver observations or reserved flight groups were opened.

[Conditioning plan](ESA_CONDITIONED_TANGENT_PLAN.md) ·
[Finite-step plan](ESA_CONDITIONED_WITNESS_PLAN.md) ·
[Full affine comparison](esa-conditioned-calibration-contrast.json)

The conditioned study is `esa-conditioned-tangent-v1-20261118`, with
manifest SHA-256
`580f297f0f8fd1b944edd2d21a53bdc248d8d1552cea3649e4894204745b62fe`.
It retains `full-factors.npz` and `conditioned-tangent.json` per
model. The finite-step study is `esa-conditioned-witness-v1-20261118`,
with manifest SHA-256
`52cddc2cdfdd4bfc5cec3ae5d46313416b1d87c60e19108a24ec66979c6a772a`.
Its three `conditioned-witnesses.json` records contain all 24 exact
checks, including the four original steps that exceeded the allowance.
