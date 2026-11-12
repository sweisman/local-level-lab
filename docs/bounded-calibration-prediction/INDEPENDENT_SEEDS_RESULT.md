# Two new noise draws: bound-aware aircraft check

**48/48 cases returned; 48 technical, 48 numerical and 48 withheld-position accuracy checks passed. 48 passed both required numerical and accuracy screens.**

| Seed | Returned | Technical | Numerical | Accuracy | Combined |
|---:|---:|---:|---:|---:|---:|
| 314159 | 24/24 | 24 | 24 | 24 | 24 |
| 161803 | 24/24 | 24 | 24 | 24 | 24 |

| Seed | Physical coordinates inside bounds | Future receiver coordinates inside bounds | Median physical width, latitude / longitude / height |
|---:|---:|---:|---|
| 314159 | 2880/2880 | 2880/2880 | 0.00078262° / 0.0006588° / 12.408 m |
| 161803 | 2880/2880 | 2880/2880 | 0.00075448° / 0.0006515° / 12.75 m |

The predeclared 48/48 method gate passed.
The full per-condition table preserves every missing, failed and passing
[case](independent-seeds-results.csv). Interval containment and width
are reported separately in that table and the verified report.

Two independent noise draws per condition are not enough to calibrate
95% interval coverage. Receiver epochs within a draw are correlated.
These are generated software checks, not observed-aircraft evidence.
Every scientific decision abstains. The original 24-case release and
its failed stopping check remain unchanged.

[Frozen plan](INDEPENDENT_SEEDS_PLAN.md) ·
[Prediction uncertainty roadmap](../PREDICTION_ERROR_LAW_PLAN.md)
