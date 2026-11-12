# Recovery route for the three-pair development study

The [paired plan](V2_PAIRED_PLAN.md) fixes three task identities, 1,206 total
native-call capacity and a four-hour cooperative wall limit. Before launch,
the source/environment-bound qualification must pass. The separate
[reboot-recovery receipt](v2-paired-recovery-report.xml) passes all five
source/environment-bound charge and interruption checks. The original
three-pair study is running under its frozen allowance. The procedure below
applies only if it closes with unfinished work.

After a reboot, inspect the canonical study status and completion record.
If all three tasks are sealed, publish them. If work is incomplete, establish
that the original workers have actually stopped; a stale PID or progress
snapshot is insufficient. Never start a second coordinator while a shard
still owns its lease.

Only after verified worker exit, close the original terminally without
refitting completed tasks. Use the qualified `lll.studies.task_resume`
procedure with the frozen recovery request. Prepare one separate finite
continuation with at most four charged attempts per unfinished task, nine
technical interruptions in total, a four-hour cooperative wall cap and a
5 GiB free-space floor. Its scientific inputs, source and numerical
environment must match the original. Then use the idempotent resume command
under a three-worker, one-thread-per-worker compute guard. Completed numerical
failures stay sealed; the continuation schedules only unfinished technical
work. Do not create a new allowance after subsequent reboots.

The commands below are for a verified interruption only; never run them while
the original worker is live. Start with the canonical status command:

```sh
~/venv/bin/python analysis/status.py --study data/esa-observed-hybrid-v2-three-pair-development
```

After confirming worker exit, close the original:

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies.task_resume close-original --parent data/esa-observed-hybrid-v2-three-pair-development --qualification-request docs/mixed-tangent-hybrid/v2-paired-recovery-request.json
```

Prepare the continuation once:

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies.task_resume prepare --parent data/esa-observed-hybrid-v2-three-pair-development --output data/esa-observed-hybrid-v2-three-pair-continuation --qualification-request docs/mixed-tangent-hybrid/v2-paired-recovery-request.json --max-attempts-per-task 4 --max-technical-interruptions 9 --maximum-wall-s 14400 --minimum-free-bytes 5368709120
```

Resume using the same command after any subsequent interruption:

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 3 --threads 1 -- ~/venv/bin/python -m lll.studies.task_resume resume --output data/esa-observed-hybrid-v2-three-pair-continuation
```
