# How much calibration can move the saved ESA forecasts together

On ESA recording 187, the original training weights reproduced the
earlier derivative columns for all three models. The check then searched
all 27 calibration coordinates, within the original limits and a
0.10 normalized change per coordinate. It asked how far each model
could move toward the other models while keeping the increase in
earlier training loss below a common allowance.

| Pair of raw predicted paths | Nominal separation, RMS | Upper bound on closure, allowance 0.001 | Upper bound on closure, allowance 0.01 |
|---|---:|---:|---:|
| Specified-field globe and zero-field globe | 2,588.79 m | 3.80 m | 11.60 m |
| Specified-field globe and zero-field disc | 3,996.51 m | 3.69 m | 11.28 m |
| Zero-field globe and zero-field disc | 1,440.44 m | 3.17 m | 9.96 m |

Closure is the sum of two convex bounds, rounded up, one for each model's
movement along the direction joining the two nominal paths. The bounds
apply to the affine calculation. The paths in the table are the raw
inertial forecasts before adjustment for correlated receiver error.

The nonlinear integrator replayed all 12 trial steps. Its projected
movements differed from the affine movements by at most 1.2 mm.
Only two of the trial steps stayed within their strict loss allowance
under the nonlinear integrator. The others exceeded it by up to 1.63%.
A further check needs a bound on nonlinear error across the whole
earlier-fit region. The aircraft error law still needs independent
support.

Three tasks passed with two new derivative sweeps and 15 scalar
sweeps. They reused the original specified-field tangent and training
weights. No models were refit and no later receiver observations or
reserved flight groups were opened.

[Fixed study plan](ESA_CALIBRATION_CONTRAST_PLAN.md) ·
[Original training weights](ESA_ORIGINAL_WHITENING_RESULT.md)

Closed study ID `esa-calibration-contrast-v1-20261118`. Manifest SHA-256
`b6090b845e20a82e617e05e4f00e97c342729dcecd2150a7ce4bd56e40bbb3ef`.
The three sealed `contrast-support.json` records include the feasible
affine steps, convex bounds and nonlinear checks. The two zero-field
tasks also retain their full forecast derivative arrays.
