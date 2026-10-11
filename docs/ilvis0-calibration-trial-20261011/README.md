# Z-axis calibration comparison

**Completed: 11 of 12 fits converged.** This comparison tests whether
the completed control's globe preference survives when each Z-axis gyro correction
is removed separately. An IMU (inertial measurement unit) measures turning and acceleration.

Fixing Z gain to zero completed all six fits and preserved globe over flat, then
rotating over still globe, under both processing cases. Fixing Z offset to zero
completed five of six fits: the still-globe fit with no upstream removal exhausted
its evaluation allowance. The other processing case favors globe. The complete
offset comparison remains numerically unresolved, and rotation is withheld for it.

All four rotating-globe fits converged, with horizontal error about 0.082–0.085 m
and vertical error about 0.696 m, close to the original clock reference. Their
costs increased by less than 1%. This control's close rotating-globe fit therefore
does not require either Z correction individually to reach its old limit; the
remaining free correction may still compensate. The test does not establish
the instrument's true calibration. These are repeats of one stretch, not independent
flight confirmations. The 12 starts used 1,837 evaluations and about 94 minutes
of fitting. No retries are permitted.

The target is the same preselected 7.30-minute stretch of
`ILVIS0_applanix_57300_610_LVIS_38614965.013`, IMU type 21,
median ground speed 878.1 km/h. No new flight interval is selected.

The completed [clock comparison](../ilvis0-clock-trial-20261010/README.md) is the
unchanged reference. It favors globe over flat, then rotating over still globe,
under both processing cases. Its Z gyro gain and constant offset still reach their
permitted limits. The [saved calibration audit](../ilvis0-clock-calibration-audit-20261011/README.md)
describes that behavior.

The new alternatives fix Z gain to zero or fix Z offset to zero, leaving the other
correction free within its existing limit. Zero is a diagnostic reference, not a
measured factory calibration. Each alternative receives rotating globe, still globe
and stationary disc fits under both existing processing cases. Other bounds,
packet-header timing, original optimizer, initialization and receiver covariance
remain unchanged. Interpret shape first and rotation only after consistent globe
preference under both processing cases.

The allowance is **12 starts, one per identity, at most 200 evaluations each and
no retry reserve**. At the previous measured runtime, full allowance use is roughly
**2–2.5 hours**, plus preparation/publication. One detached worker uses two numerical
threads. A durable start journal, exclusive lock, environment/source/input hashes
and atomic results support recovery without repeating interrupted starts.

[Frozen plan](PLAN.md) records the full comparison and separate future prediction
proposal. This run performs no held-out fitting or archive expansion. Completed
studies remain preserved; no statistical decision threshold is introduced.

The numerical allowance is spent. Do not relaunch the worker. To publish the
completed evidence without fitting:

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python analysis/tests/ilvis0_calibration_trial.py --package-only
```

Never launch a duplicate worker or resume completed numerical work. After completion,
`--package-only` publishes evidence without fitting.
