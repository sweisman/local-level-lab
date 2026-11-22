# Directions learned on another flight depend on the route

Choosing directions from separate generated histories leaves all
training observations available for calibration. This check tested
whether two borrowed directions still capture the differences among
the three model forecasts.

| Source of the directions | Error allowance | Median information retained in the weakest contrast | Cases retaining half or more for every model pair |
|---|---|---:|---:|
| Other histories on the same route | Full path | 67.1% | 42/48 |
| Other histories on the same route | Cubic position errors allowed | 48.5% | 36/48 |
| Histories on the other route | Full path | 19.5% | 23/48 |
| Histories on the other route | Cubic position errors allowed | 12.6% | 8/48 |

Each row covers twelve target histories and four working covariance
assumptions. All donor and target spaces had two numerical directions.
Even so, the weakest retained contrast ranged from 0.27% to 77.5% in the
same-route comparisons with cubic errors allowed. Full rank therefore
does not guarantee useful separation.

Every target seed stayed out of its own direction selection. The
comparison measured separation among forecasts and used no later
receiver observations. In this generated cohort, latitude and the
climbing or descending profile change together, so the study cannot
assign the loss to one of those features.

The result disfavors a single pair of directions borrowed across
routes. A future test can compare a predeclared wider direction space
or use independently specified route-specific geometry. Both need to
retain the contrasts on a fresh route before they can support a
calibrated decision. No aircraft was scored by this check.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.forecast_direction_transfer replay
```

[Fixed design](FORECAST_DIRECTION_TRANSFER_PLAN.md) ·
[Frozen inputs](forecast-direction-transfer-freeze.json) ·
[All 192 comparisons](forecast-direction-transfer-result.json)
