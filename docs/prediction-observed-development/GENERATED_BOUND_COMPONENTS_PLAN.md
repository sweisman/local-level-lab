# Saved generated interval-width decomposition

Use only the two closed bound-aware generated forecasts. Verify the sealed
artifacts, same error-operator configuration and fixed 600/300 split. Both
saved training tangents have full rank 26 and no discarded calibration
direction. Under the original marginal allowance, each interval half-width
is the sum of its calibration-ellipsoid radius and the conditional
future-noise radius. Compute the latter from the saved conditional covariance
diagonal and the declared 0.025 future alpha; subtract it from the saved
half-width to recover the former. Reject negative or inconsistent radii.

Report the median calibration fraction for north/east/up and predeclared
future indices 0, 59, 119 and 299. This is a decomposition of an **assumed
affine Gaussian bound**, not measured uncertainty or evidence that one
physical error source caused the fitted path miss. No new fit, aircraft
read, revised decision or source-study change is allowed.
