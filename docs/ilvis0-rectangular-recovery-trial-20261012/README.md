# A different bounded solver for the unresolved stretches

The [first recovery trial](../ilvis0-convergence-recovery-trial-20261012/RESULTS.md)
recovered eight unfinished primary fits but did not finish any of its three
unresolved stretches. The [saved-result audit](../ilvis0-recovery-diagnosis-20261012/README.md)
separates excessive remaining gradients from failed measurement-stability checks.

This next proposal changes how the optimizer chooses its bounded steps. The
measurements, Earth models, calibration bounds and uncertainty assumptions stay
the same. It also requires a fresh stability check and saves enough local numerical
information to diagnose another stall without repeating a complete fit.

The small software screen found a known-answer problem that reproduces one of the
earlier stopping failures. The alternative method passed that problem and all
30 screen controls. Those are software results; the new archival trial is
**approved and running** under its recorded finite allowance. Results publish
automatically on completion.

The active preparation is `data/ilvis0-rectangular-recovery-trial-v2-20261012/`,
which freezes the complete numerical-helper dependencies. The zero-start earlier
preparation is preserved and must not be launched.

The [finite plan](PLAN.md) uses the same three failure examples and completed
control: **24 starts**, at most **14,448 native sweeps**, two total numerical
threads and no retries. Estimated runtime at the ceiling is **10–14 hours**.
All planned fits, control comparisons and repeats must pass before expanding.
The original **12 globe preferences, zero flat preferences, 41 unresolved**
remains unchanged.

## Preparation and launch

From the repository root, build the software receipt, then prepare the freeze:

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python docs/ilvis0-rectangular-recovery-trial-20261012/build_controls.py
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python analysis/tests/ilvis0_rectangular_worker.py --prepare-only
```

Only after approving this finite allowance, record authorization and launch as
separate commands:

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python analysis/tests/ilvis0_rectangular_worker.py --record-authorization
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python analysis/tests/ilvis0_rectangular_worker.py --detach
```

The worker preserves shared locks, source/input/environment checks, charged
journals and atomic results. It publishes automatically on completion.
`--package-only` publishes completed outputs without refitting. Do not resume a
completed trial or spend its unused allowance elsewhere.
