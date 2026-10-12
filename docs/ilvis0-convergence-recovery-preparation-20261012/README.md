# Numerical recovery of the 41 unresolved stretches

This is the next priority after the active receiver-correlation/prediction comparison.
Further diagnostic expansion is deferred. The purpose is to complete as many of
the existing 41 unfinished model comparisons as possible, retaining their selected
measurements, physical models, calibration bounds and two processing cases.

All 41 were already fitted in the first pass. They are unresolved because at least
one required fit did not finish successfully. Their status is not equal model
support and does not say that the data contain no signal.

## Representative subset prepared from saved status

| Numerical failure category | Stretches | Meaning |
|---|---:|---|
| Every unfinished fit passes saved stationarity | 7 | Saved gradients are small enough, but solver completion is missing. |
| Mixed stationarity | 16 | Some unfinished fits pass the saved gradient check and others do not. |
| No unfinished fit passes saved stationarity | 18 | More optimization is needed under the saved local check. |

Passing saved stationarity does not establish objective stability, a global
optimum or permission to relabel a failure. These categories only guide the
numerical recovery test.

[All unresolved stretches](all-unresolved.csv) retain exact source hashes, UTC
intervals, duration, speed, recorded IMU type and original selection provenance.
[The representative subset](representative-subset.csv) contains the earliest UTC
interval in each failure category, with filename and segment ID as deterministic
tie-breakers, plus the existing completed October 5 control. Neither achieved model
costs nor a desired shape preference enters selection of the three failures.
The subset checks numerical coverage, not independent-flight replication.

## Four-step sequence

1. **Representative subset:** preserve this three-failure/one-control selection.
2. **Solver and finite budget:** prepare a separately versioned method that permits
   more evaluations and can start from preserved feasible solutions. Keep model
   equations, calibration bounds and processing assumptions fixed. Check its
   behavior on existing independent software controls. Freeze strategies, starts,
   stopping criteria, sweep ceilings and runtime estimates before requesting
   observed-data computation. Do not change the active worker or its dependencies.
3. **Qualification:** check objective agreement, valid stopping, repeatability
   and predicted tracks on the subset. Preserve every attempt and failure. More
   permissive completion flags alone are not qualification. Numerical recovery
   does not require finishing the deferred publication diagnostics first.
4. **All 41:** apply the qualified method in a separately budgeted recovery study.
   Complete all three candidates under both processing cases before calling a
   stretch resolved. Preserve the original first-pass findings and report newly
   completed comparisons separately. Some stretches may remain unresolved.

This preparation reads published saved metadata only. It makes no native
predictions, opens no NASA original and authorizes no new observed fits. The
current comparison's allowance cannot be reused for recovery. Numerical completion
and calibrated scientific support remain distinct; adequacy and uncertainty work
can be revisited after recovery.

Reproduce without numerical fitting:

```sh
~/venv/bin/python docs/ilvis0-convergence-recovery-preparation-20261012/build_selection.py
```
