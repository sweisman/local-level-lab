# Complete the interrupted ESA method comparison

The original 24-pair development study has now closed terminally under its
frozen runner: 14 sealed passing pairs, four sealed technical interruptions,
and six never-started tasks. Its manifest, saved results and charges verify.
Its original allowance and terminal status remain unchanged by the separate
continuation.

## Recovery boundary

The recovery software passed 11 focused tests, including a simulated worker
loss, a fresh-process dry run, duplicate-owner exclusion, unchanged source,
input and environment checks, and finite attempt caps. The source-bound
qualification request and test report are preserved in
`recovery-qualification/`. After confirming that no worker owned its leases,
the original allowance was closed as terminal under its existing runner. That
sealed four charged losses as technical interruptions and left six
never-started tasks uncharged. Preserve all 14 completed outcomes, including
any failures, without refitting them. A new continuation may contain only the ten identities
that lack completed outcomes. It must use the original source, inputs,
environment, model settings, numerical method, bounds and acceptance checks.
Record every earlier charge and every new technical attempt separately.

The separate ten-task continuation is now running. Its frozen limits are four
one-thread workers, a 72-hour cooperative wall ceiling, at most three total
attempts per task, at most 14 technical interruptions across the original and
continuation, and a 10 GiB free-space floor. Its idempotent resume command is:

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies.task_resume --project . resume --output data/esa-observed-hybrid-continuation-20261111
```

The [status command](../../analysis/STATUS.md) reports each stage. The original
14 passing pairs are sealed and are not part of this new execution allowance.
The read-only combined-task ledger now passes a focused test that preserves a
completed numerical failure, counts all technical attempts, and rejects a
changed completion receipt. It verifies technical coverage only; the physical
and paired-model replay in the audit plan remains required after the run.

## Qualification before a long run

Use the shared `lll.studies` lifecycle. Before preparing a continuation, test
an idempotent resume command against a finite simulated worker interruption
and a new process. It must reject duplicate owners, changed inputs, changed
source or environment, exhausted recovery caps and any attempt to requeue a
completed numerical failure. Freeze per-task and whole-study technical recovery
caps, start/evaluation limits, a cooperative wall ceiling and at most four
total numerical threads. If this qualification fails, launch no continuation.

Each resume first verifies the parent and all prior stages, including their
hashes, charges, seals and leases. It schedules only unfinished work. A
completed numerical failure remains a completed result; only a verified
technical interruption can receive a separately charged retry. The recovery
command must be safe to repeat after a notebook reboot.

## Result and publication gate

After the continuation closes, audit all 24 identities together: 14 original
sealed results plus the ten continuation results. Require the same numerical,
physical-adequacy and forecast-difference checks as the original plan. Report
every failure and technical interruption. A complete substitution conclusion
requires all 24 paired comparisons to meet the fixed tolerance; otherwise
report the qualified subset and the failed gate. If the deadline or technical
attempt cap leaves a pair without a sealed result, the combined auditor records
it as missing and publishes the failed gate after verifying every closed stage.
It does not launch another fit. This remains a development
software-method test on recording 187; the reserved ESA confirmation groups
remain untouched.

[Original comparison](PLAN.md) · [Audit plan](AUDIT_PLAN.md) ·
[Recovery rules](../TASK_RECOVERY_AND_RETENTION.md).
