# Completed comparison: verified numerical stopping

**Completed: five of six fits converged; qualification did not pass.** The comparison
preserved the five completed fits but did not finish the remaining flat-disc fit.
Its local correction exceeded the declared residual-step stability limit by a factor
of 1.55. The physical data and assumptions stayed the same. See the
[matched results](RESULTS.md) and [saved failure diagnosis](../ilvis0-verified-stop-diagnosis-20261011/README.md).

An **IMU (inertial measurement unit)** records turning and acceleration. This trial uses
one saved airborne recording to qualify a numerical revision; the archive still contains
53 selected stretches. The [diagnosis](../ilvis0-solver-diagnosis-20261011/README.md)
explains why the previous attempt remains unfinished. The [plan](PLAN.md) gives the
unchanged science, stopping tests, six-start ceiling and estimated 55–65 minute budget.

Preparation and ordinary software tests start no airborne fits. The separate six-start
allowance is spent; no replication or full-corpus starts are included. Replication
over the two preselected recordings remains deferred pending numerical qualification.
No frozen failure is relabeled and no retries are authorized.

The tested `watch_report.py` completed publication automatically after the worker
finished and released its lock. Both processes are complete; do not relaunch them.
The report can be regenerated from saved metadata using `build_report.py` with
`PYTHONPATH=analysis`; it performs no fits or retries.
