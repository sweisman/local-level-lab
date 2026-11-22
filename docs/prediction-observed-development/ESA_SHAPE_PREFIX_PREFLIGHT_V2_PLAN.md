# Check the faster source-error calculation on the same ESA packets

Reuse byte-identical prefix inputs and reference metadata from the
[first preflight](ESA_SHAPE_PREFIX_PREFLIGHT_RESULT.md). Replace the
repeated rational arithmetic in the source-error transfer with exact
binary-fraction arithmetic and one final outward rounding. Require
the same position checks, derivative columns, packet limits and
50-second allowance for each model as in the original plan.

Keep both earlier results and their charges. This new run tests the
revised implementation and has its own two bound calls. It uses no new
native forecasts, fits, or reserved data.

[Original plan and criteria](ESA_SHAPE_PREFIX_PREFLIGHT_PLAN.md).

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_shape_prefix_preflight --reuse-prefixes
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies run \
  data/esa-shape-prefix-preflight-v2-20261119 --reserved-threads 0
```
