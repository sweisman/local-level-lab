# Saved vibration-failure diagnosis

The [frozen generated check](RESULT.md) had four whole-history
exceedances, all in its 128-case vibration stratum. This report
reads only their archived forecasts and scores. It makes no new
simulation or fit.

| Seed | Second | Axis | Signed standardized error | Assigned σ | Absolute error |
|---|---:|---|---:|---:|---:|
| 2026111852 | 69 | N | +4.077 | 0.1635 m | 0.6665 m |
| 2026111926 | 61 | U | -3.881 | 0.0421 m | 0.1634 m |
| 2026111938 | 61 | N | -4.115 | 0.0421 m | 0.1733 m |
| 2026111964 | 61 | U | +3.654 | 0.0421 m | 0.1539 m |

Three maxima occur at the first withheld second (61); the fourth
at second 69. The largest standardized error is concentrated near
the forecast boundary, not at the 120-second endpoint. The median
whole-history maximum is 1.807 without vibration and 1.850 with
vibration. A one-sided Fisher comparison of four versus zero tail
counts gives p ≈ 0.061; this exploratory, post-outcome comparison
does not establish vibration as the cause. The fixed error law
still failed its predeclared generated coverage gate.

At the first withheld second, standardized error RMS is close to
one in each coordinate for both 128-case strata:

| Physical vibration | North RMS | East RMS | Up RMS |
|---|---:|---:|---:|
| off | 1.061 | 0.976 | 0.974 |
| on | 1.048 | 1.030 | 1.066 |

This does not show a broad first-second variance deficit. Four
tail events still prevented the frozen confidence gate from
certifying a failure probability below 5% for the vibration
stratum. A true rate below 5% remains compatible with these data.

The separate [clean 100 Hz control](CLEAN_PROPAGATION.md) finds
integration error below 0.0004 m in both motion modes. Next: use
fresh paired noise controls to examine the vibration association
and assess whether the accepted range can distinguish models.
Any changed law needs its own source freeze and new seeds.
Aircraft coverage remains unqualified.

[Machine report](VIBRATION_DIAGNOSTIC.json) · [frozen plan](PLAN.md).
