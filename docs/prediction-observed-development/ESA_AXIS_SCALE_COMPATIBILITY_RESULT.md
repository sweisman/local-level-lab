# A single scale setting can cover the four ESA steady windows

One setting put all four saved steady windows inside the error reference
under both inertial measurement error laws. Its north and east innovation
variance multipliers were **0.082**, and its height multiplier was **12.18**.
The earlier [held-out fit](ESA_AXIS_INNOVATION_SCALE_RESULT.md) selected
height multipliers between 0.368 and 1.0. The compatibility search used the
four steady outcomes together. Those scales have no held-out validation.

| Steady window | Squared standardized error at the compatible setting |
|---:|---:|
| 21856 | 352.02 |
| 32716 | 299.85 |
| 36436 | 375.06 |
| 39916 | 404.97 |

The working joint reference runs from 290.94 to 437.69. The table uses the
increment error description. The sampled-rate description agrees within
0.002 units. The multipliers apply to ordered covariance-factor slots.
They cannot tell which physical source contributes the observed error.

Across all eight windows, the six-scale search checked **1,024 boxes**
under each law. It excluded 182 and left 661 open under each law. It found
no verified setting for all eight windows within that allowance. The open
boxes also prevent a claim that such a setting is impossible. A future
search can start from the complete retained cover and propose continuous
settings in those boxes. Fitting them to all eight outcomes would still
require a separate prediction test.

Both tasks passed three software checks and finished in 24 seconds. The
steady setting also passes the original likelihood calculation. No
trajectory fit or reserved flight was used. The independent-flight gate
remains open.

[Frozen method](ESA_AXIS_SCALE_COMPATIBILITY_PLAN.md) ·
[All tested settings and remaining boxes](esa-axis-scale-compatibility-result.json) ·
[Verified run evidence](esa-axis-scale-compatibility-evidence/README.md)
