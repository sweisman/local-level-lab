# Height-aware history check on a supported reference

Keep the [original design and limits](SHAPE_GRAVITY_HISTORY_PLAN.md).
The [second version](SHAPE_GRAVITY_HISTORY_V2_PLAN.md) reached the
initial-force guard in all four tasks. At its zero reference, the independent
rounding check exceeded the stored nonlinear cap by about 3.5 × 10⁻¹⁹
at 5 ms and 1.4 × 10⁻¹⁸ m/s² at 250 ms. The guard rejected those tasks
before propagation. Their terminal results and charges remain sealed.

For this separate generated check, move the reference to 0.1 on each
normalized coordinate. Keep the box at ±0.1 around the reference and
keep all three probe positions relative to that box. Check the
initial-force cap before freezing the task. This tests how the
history bound behaves where the existing guard permits propagation.
The guard and the position-error target stay the same.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.shape_gravity_history
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies run \
  data/shape-gravity-history-v3-20261119 --reserved-threads 0
```
