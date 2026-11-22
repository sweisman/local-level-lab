# Estimating error size and persistence together improves the ESA checks

The joint error rule put **six of eight** omitted windows inside the fixed
reference, up from two. It also improved the log score on **all eight**.
The development gate requires all eight inside the reference, so it remains
unmet under both inertial error descriptions.

| Error rule | Total omitted negative log score | Windows inside reference |
|---|---:|---:|
| Saved diagonal scales | −10,725.40 | 2/8 |
| Turn-linked persistence with saved variances | −11,739.68 | 2/8 |
| Joint variance and persistence | −12,261.52 | 6/8 |

Lower scores are better. The two inertial error descriptions give the same
counts and log scores to the precision shown. The steady window at report
21856 scored **491.84**, above the reference interval of 290.94–437.69.
The turn at report 33796 scored **276.65**, below it. The hardest turn in the
earlier check, at report 41116, now falls inside the reference at **403.08**.

The retained quiet-memory estimates range from about **7.1 to 8.8 seconds**.
The motion-memory estimates range from **15 to 256 seconds**, including one
fold at the upper limit under each description. All sixteen searches reached
the 192-evaluation cap. The scoring therefore uses the best donor setting
actually visited for each fold. An independent check of their stopping
conditions is still needed.

All eight tasks finished in 44.10 seconds on two one-thread workers. Ten
software checks passed, including the exact cap and comparison with a dense
covariance. The run used no trajectory fits or reserved flights. Its measured
improvements apply to the eight windows from recording 187.

[Frozen method](ESA_JOINT_PERSISTENCE_PLAN.md) ·
[All parameters and scores](esa-joint-persistence-result.json) ·
[Verified run evidence](esa-joint-persistence-evidence/README.md)
