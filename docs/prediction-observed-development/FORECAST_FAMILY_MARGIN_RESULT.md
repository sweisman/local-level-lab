# The forecast separation survives alternate training receivers

On the opened ESA flight, switching the receiver export used for training
preserved the model ranking in an earlier six-fit check. This replay asks a
stronger question about the same nine saved forecasts. Each model can use
any mixture of its three fitted forecasts, separately from the other
model. Even then, **at least 99.1% of the original distance** remains in the
weighted forecast direction across all 24 comparisons.

| Model pair | Smallest separation across receiver choices, by covariance assumption | With cubic position errors also allowed |
|---|---:|---:|
| Specified-field globe and disc | 28.24–31.54 | 28.13–29.31 |
| Specified-field globe and zero-field globe | 22.06–25.09 | 21.95–23.66 |
| Zero-field globe and disc | 25.03–26.10 | 24.99–25.90 |

Each distance is in the same standardized units as the
[original forecast comparison](FORECAST_PAIR_INFORMATION_RESULT.md).
The ranges cover two drift laws and two receiver weighting assumptions.
The calculation holds the direction between each pair's original
forecasts fixed, then measures the smallest gap between its projected
forecast families. A positive gap shows that all mixtures stay separated
in this direction. The cubic version also allows each candidate a smooth
position error through constant jerk.

The test covers the one processing and noise setting used in the
[matched alternate refits](ESA_ALTERNATE_TRAINING_REFIT_RESULT.md).
All three exports share an antenna. A shared receiver error or
calibration change outside the saved forecasts could change the result.
The replay used earlier receiver positions and previously sealed
forecast paths. All reserved flight groups remain closed.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.forecast_family_margin replay
```

[Fixed design](FORECAST_FAMILY_MARGIN_PLAN.md) ·
[Frozen inputs](forecast-family-margin-freeze.json) ·
[All 24 comparisons](forecast-family-margin-result.json)
