# Durable sharded flight campaigns — 2026-10-06

The optional runner splits a frozen flight campaign into independent journals, uses at most
two local worker processes, and merges duplicate-checked results in deterministic task order.
Each worker starts with one BLAS/OpenMP thread. No flight simulation or campaign was launched
while developing it. Actual speedup, diagnostics storage and long-run performance remain
unmeasured. Existing prospective plans are stale after the source change.

## Preparation and scope

Implementation: `analysis/lll/campaign_shards.py`; CLI: `analysis/tests/sharded_campaign.py`;
fixtures: `analysis/tests/test_campaign_shards.py`. The existing research harness accepts
`--write-sharded-plan FILE --shards N` instead of executing a campaign. Preparation requires
`OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`, and `MKL_NUM_THREADS=1` before imports. An earlier
two-thread freeze cannot be reused under the new worker environment.

Use the same reviewed geometry, nuisance, bootstrap, domain and statistical planning arguments
as the serial research harness. Add `--write-sharded-plan` to freeze without fitting. The harness
still requires its `-o` argument, but that output is not created during preparation. Neither a
prepared plan nor this documentation authorizes execution. All current additional-attempt
allowances remain zero; a new bounded campaign needs separate authorization.

`sharded-flight-campaign-1` embeds the source/configuration/policy/environment manifest, exact
candidate jobs, primary/pair decision-file contents and fixed task axes. Candidate jobs and the
execution version are added to the scientific manifest, preventing a job list from drifting
away from its claimed configuration. The plan adds shard count and resource/recovery rules.
Tasks are computed from an implicit grid rather than materializing hundreds of thousands of
simulated designs. Order is seed, truth, scenario, candidate, geometry. Task IDs bind the manifest
and scientific arguments; changing shard count or local worker count does not change task IDs,
RNG streams or scientific settings. Modulo assignment fixes each task to one shard.

Fresh flight development/calibration/validation are supported. Summary pools and replayed
holdouts are refused. Calibration requires a frozen observable domain and all truths;
validation also requires actual frozen decision files. Public-track and magnetic two-path
empirical restrictions remain in force. The adapter calls the existing `realize` and
`flight_run` functions, including their separate RNG streams and shared eligibility rules.
Parallel execution does not estimate thresholds or promote a policy automatically.

## Explicit execution and resume

After a new budget is approved, the command shape is:

```sh
/home/sweisman/venv/bin/python analysis/tests/sharded_campaign.py run PLAN_FILE --output CAMPAIGN_DIRECTORY --workers 2 --attempt-limit APPROVED_TOTAL
```

`--attempt-limit` is mandatory and means the total allowed prefix of the frozen task grid,
including all previously started attempts. It is not a fresh allowance on each resume. Use
the same plan, output and total limit to resume. Increasing the total requires an additional
approved budget. Lowering it below already-started tasks is refused. The runner never stops
because acceptance or a model decision looks favorable. A partial prefix is marked incomplete
and is rejected as calibration/validation evidence by the shared record validator.

Add `--detach` only for an explicitly authorized background launch. The coordinator starts
in a new process session, writes its PID/command and log, and acknowledges launch only after
the child writes ready status. For Codex, launch outside the per-command sandbox using the
required escalation; otherwise the sandbox can kill children at command completion. No such
background launch occurred during this implementation.

Check status and active PIDs before resuming. Per-campaign and per-shard locks prevent duplicate
workers; orphaned workers are detected before replacements are spawned. Ordinary SIGINT/SIGTERM
stops the coordinator and its children. A killed coordinator can leave children working up to
their existing prefix budget; they keep journal locks and must finish or be stopped before resume.
Finished attempts do not need further model calls or network access to remain durable.

## Durable output corpus

Only explicitly named plan/shard files are accessed; the runner does not scan neighboring files.
The output directory contains:

| Artifact | Purpose |
|---|---|
| `plan.json` | Immutable bound plan, including the scientific manifest and decision files |
| `shard-NNN.jsonl` | Append-only, hash-chained start/completion events, fsynced individually |
| `shard-NNN.lock` | Exclusive journal writer lock |
| `shard-NNN.status.json` | Atomic progress, PID, limit and error |
| `shard-NNN.log` | Durable subprocess output |
| `shard-NNN.recovery.jsonl` | Preserved incomplete final bytes before a tail repair, if needed |
| `diagnostics/TASK_ID/` | Existing full pipeline diagnostics, separately retained per task |
| `coordinator.lock`, `launch.lock`, `merge.lock` | Coordinator, launch and reducer exclusion |
| `status.json` | Coordinator state; `budget_complete` differs from full campaign completion |
| `launch.json`, `coordinator.log` | Explicit detached-launch details/output, only if requested |
| `campaign.json`, `merge-status.json` | Deterministically ordered merged evidence and coverage |

A start event is fsynced before fitting, including the journal's new directory entry. A result
is checked against its immutable task, candidate, partition, source freeze, numerical environment,
eligibility and decision policies before its completion is fsynced. Exceptions become recorded
failed attempts. Successful and failed completions are never retried.

If a process disappears after a durable start but before a durable completion, resume records
an infrastructure failure with the original outcome unavailable. It does not rerun that task.
There is no statistical information invented for such a failure. Its lost runtime is unknown
rather than zero; merged timing reports sum known
attempt times, label that basis and count attempts with unknown runtime. They are not a measured
coordinator wall time or a complete cost estimate. Valid complete entries are
never changed. A truncated final write is saved byte-for-byte with its offset and recovery time
before truncating only those incomplete bytes. Malformed complete entries, broken hash chains,
missing/out-of-order tasks, provenance mismatches and wrong-shard records are rejected.

## Merging and verification

The coordinator merges automatically after its assigned prefix finishes. A separate `merge`
command uses the same plan/output; `--allow-partial` is required to export incomplete diagnostics.
Live writers, unrecovered starts and malformed tails block merging. The reducer reads fixed
shard journals, checks every event/record, and streams them in global task order into an atomic
campaign file. It retains all failures and exports task IDs/indices, coverage and failure counts.
It does not build a second full in-memory campaign or recompute scientific decisions. It does
not silently manufacture independence among shared seeds. Statistical calibration tools retain
their existing sample-size and holdout checks; their later processing can still need substantial
memory for a large campaign.

The focused checks include two actual OS processes writing fixture records, serial/shard
equivalence, one-thread initialization before numerical imports, concurrency limits, locks,
source drift, interrupted starts, exact tail recovery, corrupted journals, policy provenance,
partial-budget rejection and preparation that never invokes the flight pipeline. Fixture records
are software-test data, not simulated flight evidence. No distributed speedup or half-million
attempt campaign has been demonstrated; execution on other hosts needs a reviewed environment
and separate resource authorization.

Verification: **94 focused checks passed in 6.90 seconds** across the runner, observable domain,
shared eligibility, research hardening and existing development-worker recovery. The prior full
Python suite applies to the earlier wind/CI commit; it was not rerun during this stage.
