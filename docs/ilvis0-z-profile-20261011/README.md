# Joint Z-axis gain and offset comparison

This worker implements the [staged profile plan](../ilvis0-integration-audit-20261011/PROFILE_PLAN.md).
It is prepared for 27 fits, at most 5,400 native sweeps, with no retries. Preparation
does not authorize or start observed fits. Estimated full-budget runtime is 6–7 hours
with one worker and two numerical threads.

An IMU (inertial measurement unit) measures turning and acceleration. The comparison
fixes its Z-axis gyro scale correction and constant offset at nine combinations, then
fits the remaining parameters for each of the three physical models. It uses the
entire previously selected 438-second IMU21 stretch, at median speed 878.06 km/h,
from `ILVIS0_applanix_57300_610_LVIS_38614965.013`,
original integration, packet-header timing and no upstream field removal. No calibration
limits change. These limits are assumptions, not measured sensor drift.

Preparation verifies the completed reference, source/input hashes and environment,
and seals a separate manifest and source snapshots. Each new fit starts at zero in
the free normalized coordinates, followed by the frozen initialization stages.
The two fixed coordinates cannot move. Derivative diagnostics use the already counted
final tangent; no hidden integrations are needed to generate them. Two reserved
predictions save track residuals under header timing and a fixed-parameter nominal-clock
diagnostic. The second prediction is not a separately optimized clock comparison.

Focused tests cover fixed coordinates, reduced derivatives, known optima, feasible
stationarity, immutable start accounting, interrupted starts, locks and non-run modes.
They do not establish global optima for the NASA data.

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python analysis/tests/ilvis0_z_profile_worker.py --prepare-only
```

Only after separate approval of the finite run allowance, use the same environment
with `--detach`. Check its shared lock, journal and completion before any recovery.
Launch outside a short-lived command sandbox. Resume may start only uncharged
identities under the unchanged freeze. Charged interruptions remain failures.

The worker publishes saved results on completion. `--package-only` republishes
verified results without extraction, prediction or fitting. Source changes invalidate
the freeze. Preparation and publication never compile or load native kernels.

Publication retains all 27 points, failures, stationarity, remaining calibration bounds,
right singular vectors and epoch residuals. Unfinished points are upper bounds on
their unknown minima. No calibrated significance, causal rotation claim or full-archive
rollout follows from this one-recording, one-processing-case diagnostic.
