# Reliable execution before another calibration campaign

The latest campaign saved 1,813 numerically passing forecasts but lost four
unfinished starts when its execution session ended. Both starts of one required
setting were lost. The scientific method did not fail on a completed result;
the incomplete cohort cannot establish the planned uncertainty threshold.

This plan improves execution and recovery. It changes no measurements, model,
calibration bounds, optimizer rule or statistical acceptance criterion.

## 1. Preserve the closed campaign

- [x] Finish the independent audit of every saved forecast and all 7,176 planned
  rows, including the four interruptions and 5,359 unexecuted starts.
- [x] Add the 40 partial files to the verified publication receipt. Preserve
  their original bytes and identify them as unfinished work.
- [x] Verify archived replay and compact recoverable working copies. Finish
  each archive operation before starting another archive writer.

The campaign stays closed. No partial-cohort threshold, replacement result or
validation launch may be inferred from it.

## 2. Make the recovery decision reproducible

**Qualified:** the reusable `analysis/lll/studies/recovery.py` component passes
26 new deterministic checks in `analysis/tests/test_study_recovery.py`, within
a 61-check source-bound suite. It uses the existing manifest verifier, charge
journals, completion seals and exclusive leases. The
[qualification report](execution-recovery/README.md) describes its scope.

The report must distinguish an owned worker lease, a completed study, unfinished work
that can continue under its existing allowance, and a cohort that can no longer
qualify. Missing process handles alone must never authorize another worker.
Keep interrupted starts charged and never retry them. For calibration, report
when both prescribed starts of a required setting are unavailable before
spending more of the remaining allowance.

The tests cover completion and hash mismatches, held leases, missing results,
split-shard start pairs, unchanged deadlines and zero additional charges. Small
generated metadata fixtures use no aircraft inputs, new noise draws or native
model calls. `analysis/status.py --study data/<study> --recovery` exposes the
read-only check; it never launches work.

## 3. Establish a durable execution environment

**Normal submitter-exit survival qualified under a host user service:** the
[finite host-service control](execution-host-service/README.md) completed all
eight heartbeats in 16.1 seconds, with one metadata task start and zero model
work. Another command observed the worker running after submission returned.
All 35 source files and the numerical environment match. The earlier
[command-sandbox control](execution-command-sandbox/README.md) remains closed
without qualification.

Use the existing study runner and four-thread guard from an execution environment
whose lifetime is independent of an assistant session. Keep output logs, locks
and journals under the study directory. Do not copy a worker or run a second
coordinator.

Demonstrate that a harmless finite worker survives the launcher's normal exit
and can be found again through its durable state. Check this separately from
survival of a host or execution-container reset: normal parent exit is a weaker
test. Do not claim the stronger property from the weaker test. No process is
terminated as part of this qualification.

If the available environment cannot provide that lifetime, document the concrete
external launch needed before proposing another multiday run. A launcher cannot
guarantee recovery of unsaved optimizer state after a host reset.

The [host-launch template](execution-recovery/README.md#launching-a-future-approved-study)
uses the existing runner with automatic restarts disabled. Host reboot, container
reset and user-manager shutdown after logout remain unqualified lifetime limits.

## 4. Prepare a new finite release only after recovery qualifies

Before freezing that release, qualify reporting of sealed `interrupted`
outcomes and its calibration-to-validation guard. An interrupted cohort must
not acquire a threshold or handoff merely because every planned row has a
returned envelope. Preserve the earlier report and its documented legacy flag;
test the revised behavior separately without refitting saved cases.

Preserve the qualified numerical method and all closed outcomes. Any new
calibration and independent validation need their own source/environment freeze,
disjoint cohorts, finite start/evaluation limits and storage estimate. Do not
reuse unused allowances or silently add retries. No new large campaign is
started by this plan.

## 5. Retain the scientific dependencies

The [future task-recovery and retention policy](TASK_RECOVERY_AND_RETENTION.md)
adds a separate follow-up: preserve completed tasks, qualify bounded recovery of
unfinished technical work and clean up declared working files only after verified
closure. It does not alter the current release's no-retry rule.

A complete finite calibration handoff remains necessary before independent
validation. Generated-data coverage does not establish the error law of real
aircraft observations or significance of the two-stage Earth-model comparison.
The 53-stretch aircraft baseline and reserved ESA confirmation groups remain
unchanged.

[Current calibration status](FEASIBLE_PREDICTION_STATUS.md) ·
[Next analyses](NEXT_STEPS.md) · [Reproducibility](REPRODUCIBILITY.md).
