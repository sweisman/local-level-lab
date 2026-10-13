# Completing the remaining archival comparisons

The original 41 unresolved stretches contain **130 unfinished model fits**. Each
stretch requires three models under two processing cases. Existing converged fits
are preserved and reused; incomplete calculations are the recovery targets.

This metadata-only preparation records the complete workload while the
[actual-position stability trial](../ilvis0-position-stability-trial-20261013/README.md)
runs. **It is not ready to launch.** The qualification trial must finish and pass
all numerical, control and repeated-start checks before the method can be used
more widely. Neither partial success nor close track agreement bypasses that gate.

## Planned workload after qualification

| Work | New starts |
|---|---:|
| Unfinished primary fits outside the qualification subset | 115 |
| One predetermined repeated start for each of the other stretches | 38 |
| Fresh completed-control fits | 6 |
| **Total** | **159** |

The qualified subset would supply 15 recovered primaries and three repeated starts.
Its three stretches remain in the combined 41-stretch ledger, with their provenance
and results identified explicitly. The six completed control fits are run again in
the new freeze to check consistency. One repeat per stretch is a numerical robustness
check; it does not make a stretch an independent flight or establish global optimality.

The proposed ceiling is **95,718 native sweeps**: at most 600 fitting calls and two
track predictions per new start. There are no retries, replacement starts or extra
attempts for difficult results. Use one worker and two total numerical threads.
Matched first-pass timing gives a ceiling estimate of **51–76 hours**. This assumes
every start spends its entire allowance; actual runtime may be shorter. A new
runtime freeze and launcher must enforce the finite limits before execution.

## Selection and starts

[The stretch inventory](stretches.csv) preserves filenames, source hashes, UTC
intervals, duration, speed, recorded IMU type and the original failure categories.
[The task ledger](tasks.csv) records all primary recovery targets, repeated-start
checks and controls, including which subset results could be reused.

Original failed-fit status defines the primary tasks. UTC order defines the repeat
schedule; the preferred model for each repeat cycles through the three candidate
names, using the first originally unfinished fit of that model or a fixed fallback.
The subset's three already declared repeats are preserved. Model costs, shape
preferences and gyro values never choose the schedule.

New primaries start from the preserved original first-pass endpoints. Repeats use
those same endpoints with the fixed 0.01 normalized-coordinate perturbation. Fresh
controls use the qualified trial's primary endpoints. Every start and input must
be hashed before execution. Existing observations, clock, calibration bounds and
receiver-error assumptions remain unchanged.

## Reporting

The final combined ledger must distinguish original results, reused qualified
subset results and new recovery outcomes. A stretch is newly complete only when
all six required fits pass and its predetermined repeated-start check passes.
Any incomplete primary or failed repeat leaves it unresolved. Report shape first;
report the background-field comparison only after consistent globe preference.
Retain every failed or interrupted attempt. No result here is a calibrated detection.

Original published findings remain **12 globe preferences, zero completed flat
preferences and 41 unresolved stretches** during qualification. This preparation
reads saved metadata only, opens no NASA originals and starts no numerical workers.

## Reproduce

```sh
~/venv/bin/python docs/ilvis0-position-recovery-preparation-20261013/build_plan.py
```

The receipt hashes the original summary, saved inventory, immutable qualification
manifest/proposal and generated plan. It does not consume or hash mutable runtime
journals from the running trial.
