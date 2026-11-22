# Tighten the link between accelerometer bias and the force transformation

Keep the two saved ESA forecasts, the original local calibration box,
the [132 existing constraints](ESA_COUPLED_TRAINING_SCORE_RESULT.md),
the earlier GPS loss constraint and the forecast-score direction.
Compare the two assumed earlier unshared error norms, 0 and 0.1.

The earlier acceleration constraint allowed a free interval for the
product of changing bias and changing force transformation. Introduce
nine arithmetic product coordinates for the individual axis terms.
Use four necessary linear inequalities per product and six signed
acceleration consistency inequalities. These are bounds on products
of the existing calibration parameters. They add no physical
parameters. Export every coefficient and limit with outward rounding.
Retain all ten archived linked points per candidate.

Reuse the [direct support method](ESA_DIRECT_TRAINING_SCORE_PLAN.md)
with two starts per candidate and assumed error level. Use one charge
for constructing the product inequalities and checking their archived
points, then four charges for the support calculations per candidate.
Allow two one-thread workers and a 110-second cooperative wall limit.
No new trajectory fits or unused receiver observations are involved.

The calculations inherit the static map's normalized allowance of
3 × 10⁻¹⁰ and retain the earlier loss allowance. The product planes are
necessary inequalities. Aircraft integrator error and prediction
coverage still need separate qualification.

```sh
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- \
  env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_acceleration_product_score
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies run \
  data/esa-acceleration-product-score-v1-20261119 --reserved-threads 0
```
