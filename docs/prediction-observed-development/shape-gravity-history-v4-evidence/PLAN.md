# Retest the original zero-centred history

Run the original four generated cases with the same zero-centred ±0.1
calibration region, query times, native forecast checks and work allowance.
Use the outward-rounded initial-force policy to construct the reference.
This policy builds the cap before conditioning and binds it to the reference.
The initial-force guard still rejects any insufficient cap.

Reuse the exact force integrals across all four queries. Record the
number of packet visits and compare the reference positions and three
prescribed trial settings to the compiled height-aware calculation.
Keep the original failed records. This test concerns generated propagation.
It reads no flight recordings and performs no fits.

[Original plan](SHAPE_GRAVITY_HISTORY_PLAN.md) ·
[Shared force integrals](SHARED_FORCE_INTEGRALS.md).

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.shape_gravity_history
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies run \
  data/shape-gravity-history-v4-20261119 --reserved-threads 0
```
