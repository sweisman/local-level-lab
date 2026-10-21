# Preserve source derivatives in the remainder

The six-source screen completes under the original limits. All height bounds
improve, but all horizontal bounds widen. No complete prediction comparison or
aircraft fit follows directly from this result.

Develop a separate conservative interval calculation of the physical body
sources and their calibration derivatives over the declared parameter box.
Keep the literal recorded inputs, mounting matrix, all 27 physical columns and
both packet phases. Include the reference point in the convex domain used for
the derivative proof. Do not reuse an unrelated saved body Taylor radius.

For a physical source component `f`, supplied numerical center `c`, supplied
row `j`, reference `z0` and box displacement limits `w`, the mean-value bound is

`remainder <= |f(z0) - c| + sum(w[k] * sup_box |df/dz[k] - j[k]|)`.

Each supremum must have an outward enclosure. Bound the ideal source value at
the reference independently of the rounded native center. Treat clipped packet
fractions as continuous, piecewise differentiable functions and include both
one-sided slopes where the domain crosses a boundary. No hidden clock-column
drop is permitted.

First check the rotation value and derivative enclosures against independent
exact-rational references, then the source stream against independent known
answers. Only after that may a separately frozen candidate intersect these
Taylor bounds with the existing physical/training norm closures and qualify
native propagation. Preserve every center, matrix, domain binding and existing
acceptance criterion. A fresh complete comparison is required before observed
prediction work can proceed.

This development uses generated data only. It does not authorize new aircraft
starts, confirmation-data inspection, cap expansion or a claim of calibrated
coverage.
