# A tighter bound on the shared force-transform score

The nine force-transform errors come from one rotation and gain map.
Bounding their signed score together limits how much they can reduce the
globe–disc separation to **8.55 standardized units**, including the other
shared terms. The result uses a working error model built from a 3 cm
receiver covariance and a term for smooth drift.

| Candidate | Independent force limit | Coupled force-score interval |
| --- | ---: | ---: |
| Zero-field globe | 28.692 | −0.352 to 8.199 |
| Zero-field disc | 28.377 | −0.351 to 8.117 |

The separation is the disc score minus the globe score along the saved
direction. Its largest possible reduction from the force terms is therefore
the globe upper endpoint minus the disc lower endpoint. The other shared
terms together contribute less than 0.000225 standardized units.

The [frozen run](esa-force-score-evidence/README.md) evaluated 63 boxes per candidate
and retained a complete cover of the original calibration region. The
intervals contained the direct results at every corner and at the original
reference. The calculation used two bound calls and no fits or new forecasts.

The [earlier error budget](SHAPE_REMAINDER_HEADROOM_RESULT.md) leaves at
least 12.78 standardized units after the affine calibration changes
if each candidate's earlier nonlinear remainder is at most 0.1.
After charging the shared terms above, at least **4.23 units** remain
for the unshared later contribution. Under the fixed 3 cm covariance,
a uniform **1.35 cm** bound per coordinate per candidate would suffice
for that contribution. The calculation still needs to verify the earlier
nonlinear limit and the full-history unshared bound before drawing an
aircraft conclusion.

[Conversion to a coordinate bound](SHAPE_REMAINDER_METRES_RESULT.md).
