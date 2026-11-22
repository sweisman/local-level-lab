# Height-aware history check with the runner's task schema

Use the [original generated plan](SHAPE_GRAVITY_HISTORY_PLAN.md), inputs,
models and limits. All four tasks in the first version rejected the runner's
additional task fields before any numerical calls. Their terminal records
remain sealed. The revised adapter checks the declared task fields and
accepts the runner's index and shard fields.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.shape_gravity_history
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies run \
  data/shape-gravity-history-v2-20261119 --reserved-threads 0
```
