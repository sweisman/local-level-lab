# Attribute the difference between the two ESA distance checks

Use the zero-field globe and disc from the previously released profiled-removal
increment setting on development recording 187. Use their original 120 later
times, the same earlier coordinate anchor and the same nine quadratic path
directions in all four checks.

Compare both the raw training-only predictions and the conditional means saved
by the earlier [forecast pair study](FORECAST_PAIR_INFORMATION_RESULT.md).
Measure each pair first with equal weights in metres and then with the earlier
study's full drift covariance with a fixed 3 cm receiver noise term. Report the
fraction of squared separation left after projecting out smooth terms. The
weighted conditional result must reproduce the earlier quadratic result.

Use one thread, two archived forecasts, one covariance operator and four
projections. The sealed coordinate anchor and conditional means suffice.
Decode no GPS observations or original measurements. Start no trajectory fits
and open no other flight. These are comparisons under a working covariance.
The outcome cannot qualify that covariance on aircraft.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.matched_shape_metric freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.matched_shape_metric calculate
```
