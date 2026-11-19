# Bias and force product constraints narrow the ESA bound slightly

The 42 new inequalities kept all 20 linked calibration examples.
The certified upper bound on combined movement under the inequalities fell
from 79.95 to **77.77 standardized units** with no earlier unshared
error. The difference between the saved forecasts is **25.41 units**.

| Assumed earlier unshared error norm per candidate | Globe movement | Disc movement | Combined movement |
| ---: | ---: | ---: | ---: |
| 0 | 0.190–39.194 | 38.538–38.577 | 38.728–77.770 |
| 0.1 | 38.668–39.781 | 38.698–38.738 | 77.366–78.518 |

The lower endpoints come from feasible points under the saved
inequalities. The upper endpoints come from checked certificates.
Even without an earlier unshared error, the disc example alone can
move farther than the nominal difference while meeting the relaxed
constraints. Physical realizability remains open.

Five of eight solver starts reached their iteration limit. Their
directions still produced valid upper bounds. At zero earlier unshared
error, neither new globe proposal yielded a verified feasible point,
so the lower endpoint uses the earlier linked example. Both candidate
tasks completed their [frozen checks](ESA_ACCELERATION_PRODUCT_SCORE_PLAN.md).
There were no new trajectory fits or later receiver reads.

The next useful comparison is to tighten the static map over smaller
physical ranges while preserving their complete union. Another solver
revision under the same inequalities cannot rule out the feasible
movement already measured here.

Both candidates give the same starting point for that subdivision.
Weighting the derivative interval widths of shared acceleration and
force by their influence on the earlier GPS loss ranks the three
attitude coordinates first. The vertical-axis attitude coordinate
ranks highest by a factor of about 5.5 over the next coordinate.
This ranking chooses where to divide the original box. The bound must
still cover every part.

[Sealed inputs, products and results](esa-acceleration-product-evidence/README.md).
