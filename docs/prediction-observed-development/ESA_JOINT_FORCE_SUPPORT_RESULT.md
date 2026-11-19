# Linking the force calibration leaves most of the ESA uncertainty

The same physical force transform now applies to earlier and later GPS
scores. Both candidates reproduced all three previous bounds exactly
before applying the physical constraint.

| Assumed earlier unshared error norm per candidate | Previous combined upper bound | Combined upper bound with the linked force map |
| ---: | ---: | ---: |
| 0 | 103.030 | 102.623 |
| 0.1 | 102.703 | 102.443 |
| 1 | 104.928 | 104.290 |

All values are standardized units under the working covariance. The
nominal separation between the globe and disc forecasts is **25.41**.
The rest of the bound, with the force transform's contribution removed,
still totals at least **102.43** across the two candidates in each scenario.
Tightening the force calculation further cannot close that gap in these
directions.

At an assumed earlier unshared norm of 0.1, the projected training-loss
constraint contributes **60.80** units to the combined bound and the 27
physical parameters contribute **41.64**. The clock, lever, reference
acceleration and force terms together contribute less than 0.006.
Those are terms in an upper-bound calculation. They do not measure how
far a physically possible calibration actually moves either prediction.
The next check should find feasible calibration changes on the saved
design and compare their scores with this upper bound.

The [frozen calculation](ESA_JOINT_FORCE_SUPPORT_PLAN.md) completed both
cases and all six bounds at 63 box evaluations each. It started no new
fits and opened no later receiver positions or reserved flight groups.
The bounds still assume an earlier unshared error limit and omit later
unshared error. The aircraft comparison remains unresolved under this
calibration check.

[Sealed inputs, source and results](esa-joint-force-support-evidence/README.md) ·
[Exact bound decomposition](esa-joint-force-decomposition.json).
