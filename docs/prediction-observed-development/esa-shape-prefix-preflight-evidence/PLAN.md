# Test the interval predictor at the archived ESA packet rate

Use the sealed zero-field globe and disc fits on ESA recording 187.
Rebuild their original initial states using the earlier observations,
as in the [scalar replay](ESA_TANGENT_REMAINDER_PLAN.md). Keep all
27 calibration coordinates and their original limits. Intersect those
limits with a radius of 0.1 in each normalized coordinate around the
saved fit.

Use the first two original query times, approximately 0.55 and 1.55
seconds. Retain all original packets needed to cover both queries
across the full local clock interval. Check both predicted centres
against the sealed forecasts with a one-micrometre tolerance. Keep
the reported position remainders and the complete set of physical
and auxiliary derivative columns.

Use the outward-rounded reference, height-dependent gravity and the
shared force integrals. Each model permits one bound call, up to 640
input packets and up to 1,280 packet steps. Use two workers with one
thread each, a cooperative limit of 50 seconds per bound and a
120-second study allowance. No new native forecasts, fits, later
receiver positions or reserved groups enter this check.

This is a saved-input development check. Its first two queries cannot
establish an error bound over the whole earlier-fit region or validate
an aircraft covariance law.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_shape_prefix_preflight
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies run \
  data/esa-shape-prefix-preflight-v1-20261119 --reserved-threads 0
```
