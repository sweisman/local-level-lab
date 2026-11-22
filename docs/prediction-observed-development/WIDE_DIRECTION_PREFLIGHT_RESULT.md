# Wider forecast tests recover separation but do not resolve every model pair

A space learned from twelve independent donor histories was tested on
two separately archived target routes. The full 24-direction space
retained **at least 97.1% of the squared distance** between every model
pair under the four working covariance assumptions. No tested width met
the illustrative 80% power requirement for every model pair and
assumption, even with the target forecast means treated as exact.

| Target and error allowance | Lowest retained fraction with 2 directions | Lowest retained fraction with 24 directions | Covariance assumptions where all three pairs reach 80% power, best tested width |
|---|---:|---:|---:|
| Straight, full path | 8.7% | 99.6% | 2/4 |
| Straight, cubic position errors allowed | 59.9% | 99.9% | 2/4 |
| Turning, full path | 9.5% | 97.1% | 2/4 |
| Turning, cubic position errors allowed | 0.2% | 98.5% | 0/4 |

The power calculation uses an upper-tail Gaussian squared-error test at
an illustrative 1% size. Adding directions can retain more separation
while also increasing the reference threshold. The replay also
calculated the most powerful one-direction test for each sealed pair.
For the turning route with cubic errors allowed, its power fell as low
as **3.6%** for the two globe variants under one covariance assumption.
In that comparison the fixed forecast paths themselves offer too little
separation at the stated noise level.

The two target routes share one seed, which was absent from the donors.
These are paired generated controls, not independent estimates of
aircraft power. The result shows why a future campaign needs a way to
identify informative route and error conditions before fitting. A
larger borrowed space alone cannot solve the weak comparisons. All
80 comparisons used earlier forecasts and opened no reserved flights.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.wide_direction_preflight replay
```

[Fixed design](WIDE_DIRECTION_PREFLIGHT_PLAN.md) ·
[Frozen inputs](wide-direction-preflight-freeze.json) ·
[All widths and model pairs](wide-direction-preflight-result.json)
