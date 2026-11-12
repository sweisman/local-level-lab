# Saved-fit ESA method failures

The faster tangent method remains unqualified: 21 of 24 paired
cases passed its original gate. This diagnostic reads only sealed
fit and forecast artifacts; it makes no new fits or scientific
decision.

| Case | Wide / faster evaluations | Largest parameter difference | Largest forecast difference |
|---|---:|---|---:|
| flat_still-0-reported-short-v1-1 | 94 / 90 | position_z (2.87188e-05 normalized) | 0.0331615 m |
| flat_still-0-reported-persistent-v1-0 | 72 / 72 | position_x (1.31568e-05 normalized) | 0.0167151 m |
| flat_still-1-reported-short-v1-0 | 88 / 88 | accel_gain_y (3.31626e-09 normalized) | 3.7259e-06 m |

Parameter differences describe the optimizer outcomes; they
do not identify which derivative column caused them. A same-point
column comparison is still needed before revising the method.

[Original gate](combined/README.md) · [Machine-readable measurements](FAILURE_DIAGNOSTIC.json).
