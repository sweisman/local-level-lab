# The earlier ESA forecast underestimated later error

The earlier error scale was too small for a later forecast of the same
length on ESA recording 187. Across four covariance assumptions, the
later squared standardized error was **3.31–3.70 times** the earlier error.
That is **1.82–1.92 times** on a root-mean-square scale.

| Error assumptions | Earlier variance as a fraction of nominal | Later variance as a fraction of nominal | Later ÷ earlier |
|---|---:|---:|---:|
| Full drift, fixed 3 cm weights | 0.00826 | 0.03018 | 3.65 |
| Full drift, reported precision | 0.00617 | 0.02046 | 3.31 |
| Reduced drift, fixed 3 cm weights | 0.00830 | 0.03073 | 3.70 |
| Reduced drift, reported precision | 0.00621 | 0.02100 | 3.38 |

These ratios compare the same specified-field globe and zero-removal
assumption at both origins. Each forecast scored 120 receiver reports.
The two IMU noise descriptions give the same results to the displayed
precision. The earlier forecast's scores were sealed before the later
scores were read for this comparison.

The same scale estimates also fall short for the two complete matched-model
settings, which fit a possible background-field removal fraction. Scaling
each error assumption by its own earlier estimate leaves all candidates
above the provisional upper reference limit in both settings. The decision
remains an abstention. Both later zero-removal matched-model settings
retain their original numerical failures.

The two periods share a flight and instrument. The later fit includes the
earlier scoring observations, so these ratios describe transfer on this
recording and provide no independent-sample error rate. The result shows
that a smaller shared variance chosen from the earlier window does not
solve the absolute-fit problem. The next error model needs to allow
earlier-to-later changes and distinguish them from changes in fit error.

From the repository root, run the three stages in order.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_rolling_scale_transfer freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_rolling_scale_transfer estimate
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_rolling_scale_transfer compare
```

[Fixed design](ESA_ROLLING_SCALE_TRANSFER_PLAN.md) ·
[Frozen inputs](esa-rolling-scale-transfer-freeze.json) ·
[Earlier scores](esa-rolling-scale-transfer-earlier.json) ·
[Full comparison](esa-rolling-scale-transfer-result.json)
