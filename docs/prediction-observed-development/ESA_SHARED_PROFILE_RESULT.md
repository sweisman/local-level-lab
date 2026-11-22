# Which shared calibration terms reach the ESA shape score?

Recovered all 24 shared calibration columns at all 520 saved queries
for both zero-field models. The scalar integrator reproduced all 1,040
saved positions exactly. At the first two queries, the reconstructed
columns matched the interval predictor within 2.3 × 10⁻¹⁶ m per
coordinate. The [frozen reconstruction](ESA_SHARED_PROFILE_PLAN.md)
used four scalar calls and two shared force scans. It performed no fits.

Using one value per shared column across the record, the later shape
score receives the following bounds in standardized units.

| Shared terms | Globe, independent by report | Globe, linked | Disc, independent by report | Disc, linked |
| --- | ---: | ---: | ---: | ---: |
| Clock–velocity and lever | 70.31 | 0.000101 | 82.66 | 0.000125 |
| Reference acceleration | 6,612,401 | < 0.000000003 | 6,542,707 | < 0.000000003 |
| Force transform | 2,160,086 | 28.692 | 2,145,869 | 28.377 |

The [score check](ESA_SHARED_PROFILE_SCORE_PLAN.md) uses the fixed 3 cm
receiver covariance. Earlier reports enter through their effect on the
later score. It sums each column's signed effect before taking its
magnitude. Most of the clock, lever and acceleration effects cancel
under that operation.

The nominal shape distance is **25.41** under this working covariance.
The force-transform bound is too wide to certify that distance. Those
nine entries come from one rotation and gain map. The next calculation
needs to keep that physical dependence and the earlier-fit constraints.
The [coupled force bound](ESA_FORCE_SCORE_RESULT.md) now limits the total
shared reduction to 8.55 standardized units. The earlier-fit and unshared
full-history error bounds remain open.

[Signed coefficient bounds](esa-linked-shared-score.json) ·
[Frozen coefficient evidence](esa-shared-profile-evidence/README.md).
