# Recovery of the rolling-origin development run

The original 48-task study is `data/ilvis0-rolling-origin-development-v1`.
Its four workers each use one numerical thread. The source/environment-bound
qualification passed 43 checks, and the separate task-continuation receipt
passed its five required reboot/charge tests. The original six-hour allowance
and every completed result or failure remain fixed.

After a reboot, first inspect the canonical status:

```sh
~/venv/bin/python analysis/status.py --study data/ilvis0-rolling-origin-development-v1
```

If it is complete, verify and publish its saved results. If it is incomplete,
establish that the original worker processes have stopped; a stale snapshot or
PID alone is insufficient. Do not launch a second coordinator while any shard
still owns its lease. Once the workers have stopped, close the original as a
terminal record without refitting its completed tasks:

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies.task_resume close-original --parent data/ilvis0-rolling-origin-development-v1 --qualification-request docs/prediction-rolling-origin/recovery-request.json
```

The **separate finite continuation** is predeclared here, before any
interruption is known: at most four charged attempts per unfinished task, at
most 144 total technical interruptions, a six-hour cooperative continuation
window, at least 5 GiB free disk, and no smoke tasks. It reuses the unchanged
scientific input, method, source and numerical environment. Prepare it once:

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies.task_resume prepare --parent data/ilvis0-rolling-origin-development-v1 --output data/ilvis0-rolling-origin-development-v1-continuation --qualification-request docs/prediction-rolling-origin/recovery-request.json --max-attempts-per-task 4 --max-technical-interruptions 144 --maximum-wall-s 21600 --minimum-free-bytes 5368709120
```

Then use the idempotent resume command. It checks hashes, journals, charges,
the continuation freeze and leases before scheduling unfinished work. On a
later reboot, inspect status again and rerun this **same** command; do not
prepare a new allowance or reset the old one.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 4 --threads 1 -- ~/venv/bin/python -m lll.studies.task_resume resume --output data/ilvis0-rolling-origin-development-v1-continuation
```

Scientific failures remain failures. The continuation applies only to
unfinished technical work and does not change the 48-task question or the
original results.
