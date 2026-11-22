# A smooth offset does not explain the later score increase

On ESA development recording 187, the later forecast scored 3.31–3.70
times worse than the earlier forecast on the same weighted squared-error
scale. Allowing a separate cubic position trend in each coordinate left a
ratio of **3.40–3.75**. The cubic terms accounted for **2.15–2.66%** of the
earlier score and **0.20–1.23%** of the later score.

| Error assumptions | Later ÷ earlier, full score | Later ÷ earlier, after cubic projection |
|---|---:|---:|
| Full drift, fixed 3 cm weights | 3.65 | 3.73 |
| Full drift, reported precision | 3.31 | 3.40 |
| Reduced drift, fixed 3 cm weights | 3.70 | 3.75 |
| Reduced drift, reported precision | 3.38 | 3.43 |

The table shows the increment-based noise calculation. The point-based
calculation agrees at the displayed precision. The replay recovered all
16 sealed whole-path scores and checked constant, linear, quadratic and
cubic changes. The percentages refer to the **weighted scores after
the original receiver conditioning**. They can differ from the share of
ordinary position error in metres.

These trends were fitted to the withheld forecast errors for diagnosis.
The saved forecasts and their decisions remain as recorded. The result
rules out a simple position offset through constant jerk as an explanation
of the weighted score increase in these windows. The remaining change
could still involve receiver error common to all exports, sensor error,
calibration, or trajectory errors with a different time pattern. Those
components need separate constraints before drawing aircraft conclusions.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.forecast_smooth_error replay
```

[Fixed design](FORECAST_SMOOTH_ERROR_PLAN.md) ·
[Frozen inputs](forecast-smooth-error-freeze.json) ·
[All scores and decompositions](forecast-smooth-error-result.json)
