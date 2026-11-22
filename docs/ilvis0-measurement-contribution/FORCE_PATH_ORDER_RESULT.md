# A closer GPS trajectory fit left the force gaps unresolved

Fourth-degree paths fit the recorded heights more closely on the same 991
windows. Median height residual RMS dropped from **0.585 to 0.216 m** on
IMU8 and from **0.354 to 0.125 m** on IMU21, across the two GPS motion inputs.

| Force calculation | Range of the 24 fitted training gaps | Profiles with zero training gap |
|---|---:|---:|
| Quadratic path with timing bounds | 0.0487–0.0838 m/s² | 0 / 24 |
| Fourth-degree path with timing bounds | 0.0160–0.0543 m/s² | 0 / 24 |
| Quadratic path with sampled mean | 0.0487–0.0838 m/s² | 0 / 24 |
| Fourth-degree path with sampled mean | 0.0483–0.0863 m/s² | 0 / 24 |

The fourth-degree enclosures reduced all 24 training gaps. The comparison
using sampled means improved 16 of 24 training profiles and 12 of 24 later
profiles. A closer fit to GPS height therefore gives limited evidence about
the force error. The enclosures allow timing offsets, variation within a
subinterval and relaxation of dependence between coordinates. Smaller gaps
with those enclosures alone cannot establish improved force accuracy.

The [frozen comparison](FORCE_PATH_ORDER_PLAN.md) keeps the two GPS motions,
two clocks, original timing allowance and both field assumptions. Each
calibration uses one nonnegative gain fit on the training windows and held
fixed later. The measured upper bounds apply to packet-averaged force.
An explicit within-packet direction bound is needed for an upper bound on
continuous force. [Force averaging](FORCE_AVERAGING.md).

There were zero new position solves or inertial fits. This comparison leaves
the sources of the force gaps and any shape decision open.

[Window results](force-path-order-windows.json.gz) ·
[Profile receipt](force-path-order-receipt.json).

```sh
~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- \
  env PYTHONPATH=analysis ~/venv/bin/python -m lll.ilvis0_force_path_order replay
```
