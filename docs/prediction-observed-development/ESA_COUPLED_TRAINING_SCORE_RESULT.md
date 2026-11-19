# Whole-box calibration constraints leave the ESA shape bound unresolved

The complete static map kept all 20 linked examples inside its 132
inequalities. The coefficients and rounded inequalities were checked
before computing bounds for the same two saved forecasts.

| Assumed earlier unshared error norm per candidate | Globe upper bound | Disc upper bound | Combined upper bound |
| ---: | ---: | ---: | ---: |
| 0 | 57.305 | 62.975 | 120.279 |
| 0.1 | 57.379 | 63.050 | 120.428 |

The combined bound still exceeds the **25.41-unit** forecast difference.
The [previous force-specific bound](ESA_JOINT_FORCE_SUPPORT_RESULT.md)
is tighter at **102.44 units** in the 0.1 scenario. The new inequalities
approximate the complete nonlinear map over one whole parameter box.
The result gives no basis for concluding that a physical calibration
can erase the forecast difference.

The rounded inequalities already exclude both saved examples that let
shared terms vary independently. The globe example violated seven
static-map, three consistency and one orientation inequality. The
disc example violated nine, three and three, respectively. Reaching
a tighter bound now requires checking how much freedom remains under
all the constraints together.

Both candidate calculations completed, including all 16 linear-program
proposal rounds per scenario and their exact arithmetic checks.
[Frozen plan](ESA_COUPLED_TRAINING_SCORE_PLAN.md)

On the two saved [calibration examples](ESA_CALIBRATION_WITNESS_RESULT.md),
the reference-acceleration remainder accounts for **90%** of the jump
in earlier GPS loss for globe and **79%** for disc. Changes to the force
transform account for another **10%** and **20%**, respectively. These
shares include interactions between terms in those two examples.
[Loss breakdown](esa-calibration-linkage-loss.json)

First check whether a more direct support calculation tightens the
bound under the current constraints and earlier GPS loss limit.
Then refine the acceleration and force relationship if the feasible
region remains wide. The full integrator's error and independent
aircraft coverage remain open.

[Sealed inputs, cuts and results](esa-coupled-training-score-evidence/README.md).
