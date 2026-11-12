# Recovery route for the four-group transfer study

The prepared study has 16 fixed task identities, at most 3,216 original native
calls, one numerical thread and a cooperative twelve-hour wall limit. Its
[source/environment qualification](qualification-report.xml) passed 24 tests.
The separate [recovery qualification](recovery-report.xml) passed all five
source/environment-bound interruption and accounting checks. No interrupted
start can be erased or silently retried; completed numerical failures remain
sealed.

After a reboot, first inspect the canonical status and completion record:

```sh
~/venv/bin/python analysis/status.py --study data/ilvis0-four-group-transfer-v1
```

If the original study is complete, verify and publish its saved results; do
not restart it. If it is incomplete, establish that the original worker has
actually exited and no shard lease is held. A stale PID or progress file alone
does not prove exit. Never start another coordinator while the first is live.

Only after verified exit, close the original without refitting completed tasks:

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies.task_resume close-original --parent data/ilvis0-four-group-transfer-v1 --qualification-request docs/prediction-group-transfer/recovery-request.json
```

Prepare **one** separate continuation for unfinished technical work. It
allows at most three charged attempts per task across the original and
continuation, at most 24 technical interruptions overall, a twelve-hour
cooperative wall limit per continuation stage, and a 5 GiB free-space floor.
It requires the same scientific inputs, source files and numerical environment:

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies.task_resume prepare --parent data/ilvis0-four-group-transfer-v1 --output data/ilvis0-four-group-transfer-v1-continuation --qualification-request docs/prediction-group-transfer/recovery-request.json --max-attempts-per-task 3 --max-technical-interruptions 24 --maximum-wall-s 43200 --minimum-free-bytes 5368709120
```

The following command is idempotent after an interruption. It verifies the
sealed evidence, charges and leases before scheduling only unfinished tasks.
Reserve the other active numerical threads when launching; the example below
assumes three are occupied by ESA:

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 --reserved-threads 3 -- ~/venv/bin/python -m lll.studies.task_resume resume --output data/ilvis0-four-group-transfer-v1-continuation
```

Do not use this route to rerun a sealed numerical failure, alter the original
3,216-call allowance, or choose a forecast by its later error.
