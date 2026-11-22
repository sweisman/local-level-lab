# How close the receiver windows are to the motion limit

The fixed receiver-only rule accepts a local window when its reported vertical
velocity varies by at most **1 m/s**, alongside separate speed, course and
completeness checks. This saved-data audit measures each window's distance from
that vertical limit. It does not rerun selection or read an IMU.

| Window category | Total | Within 0.02 m/s of limit | Within 0.10 m/s |
|---|---:|---:|---:|
| Chosen windows at supported target times | 2,194 | 74 | 398 |
| Candidate windows rejected for vertical variation | 1,416 | 108 | 453 |

The 1,416 rejected windows are **candidates**, not distinct flight times. The
study examined three candidate widths at each of 2,365 target times. It
accepted 2,194 times and rejected 171; all 52 decoded stretches had at least
one accepted time. The [per-target table](vertical-margins.csv) retains all
7,095 candidate-window spans, signed margins, original rejection reasons and
originally chosen widths. Its [hash receipt](margin-receipt.json) binds the
table to the sealed inventory and this reporter.

If every reported vertical velocity were perturbed by at most ε m/s, a
window's span could change by at most 2ε m/s. For example, 0.05 m/s per epoch
could move a span by at most 0.10 m/s. The table shows proximity to one
threshold; it **does not** estimate the actual receiver error, prove that a
window would flip, or account for the course and speed checks. The matched
gyro/accelerometer study still needs an observational error model and a check
of selection uncertainty. No original interval or model result changes.

Run the saved-only report again with:

```sh
PYTHONPATH=analysis ~/venv/bin/python -m lll.ilvis0_receiver_support_margin_report
```

[Original window inventory](README.md) · [Frozen margin question](MARGIN_PLAN.md).
