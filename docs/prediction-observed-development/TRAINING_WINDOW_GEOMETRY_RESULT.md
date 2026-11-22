# Splitting the ESA training interval weakens calibration

The software can separate direction selection from calibration by
using two earlier windows. On the opened ESA flight, keeping only
the last 200 of 400 receiver reports for calibration retained full
numerical rank in **all 20 converged fits**. It still lost nearly all
the local information in the weakest parameter combination.

| Earlier reports used to choose directions / estimate calibration | Information retained in the weakest combination | Median across parameter combinations | Largest local standard-error multiplier |
|---|---:|---:|---:|
| 200 / 200, 20 saved fits | 4.4–7.3 billionths | 2.6–2.8% | 11,700–15,000 |
| 200 / 400, two longer specified-field fits | 20.6 billionths | 48.7% | 6,960–6,970 |
| 400 / 200, same two longer fits | 0.138 billionths | 19.1% | 85,200 |

Each comparison holds the fitted point and sequential whitening fixed.
It measures the change in the derivative information after removing
the first window from calibration. The standard-error multiplier is
the worst one over local calibration contrasts. It does not measure
metres of forecast error or say that every parameter becomes equally
weak.

In the 400-report fits, the last 200 reports retain **5.5–5.8%** of
the conditional Z gyro-bias information and **1.4–1.6%** of the vertical
accelerometer-bias information. Those calculations allow all other
parameters to vary. The four original nonconverged fits remain in the
record without a split result.

This makes the simple split a poor default for this flight. Directions
set in advance using independent geometry or generated controls would
allow calibration to use the complete training interval. Those directions
still need tests for signal retention and aircraft error. The derivatives
in this audit came from fits to the full intervals, so the audit leaves
both forecast coverage and independent validation open.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.training_window_geometry replay
```

[Fixed design](TRAINING_WINDOW_GEOMETRY_PLAN.md) ·
[Frozen inputs](training-window-geometry-freeze.json) ·
[All 24 split comparisons](training-window-geometry-result.json)
