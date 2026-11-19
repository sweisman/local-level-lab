# Recovery of the twenty-group forecast study

The frozen original has 80 task identities, at most 16,080 native calls,
four one-thread workers and a six-hour cooperative wall cap. Its
[source/environment qualification](remaining-qualification-v2-tests.xml)
passed 13 tests. A separate
[recovery qualification](remaining-recovery-tests.xml) passed all five
interruption, duplicate-owner, source and accounting checks. Completed
numerical failures remain sealed and count in the 80-task denominator.

After a reboot, inspect the canonical status first:

```sh
~/venv/bin/python analysis/status.py --study data/ilvis0-remaining-prediction-transfer-20261118
```

If the completion record exists and all 80 tasks are sealed, verify and
publish the saved results. Do not relaunch the original. If it is incomplete,
first establish that the old coordinator and all worker leases have really
exited. A saved PID or stale progress snapshot is insufficient. Never start
a second coordinator while the first is live.

After verified exit, seal the original without repeating completed work:

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies.task_resume close-original --parent data/ilvis0-remaining-prediction-transfer-20261118 --qualification-request docs/prediction-group-transfer/remaining-recovery-request.json
```

Prepare one separate continuation for unfinished technical work. It retains
the same source, inputs, environment and scientific method. Its finite limits
are three charged attempts per task across original and continuation, at most
160 total technical interruptions, one six-hour continuation wall allowance
and a 5 GiB free-space floor:

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies.task_resume prepare --parent data/ilvis0-remaining-prediction-transfer-20261118 --output data/ilvis0-remaining-prediction-transfer-20261118-continuation --qualification-request docs/prediction-group-transfer/remaining-recovery-request.json --max-attempts-per-task 3 --max-technical-interruptions 160 --maximum-wall-s 21600 --minimum-free-bytes 5368709120
```

The resume command is idempotent: it verifies source and input hashes,
environment, charges, sealed results and exclusive leases before assigning
only unfinished work. Run it only when no other numerical threads are active:

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 4 --threads 1 -- ~/venv/bin/python -m lll.studies.task_resume resume --output data/ilvis0-remaining-prediction-transfer-20261118-continuation
```

An interruption does not permit rerunning a sealed failure, changing a cut,
choosing a start by later forecast error or exceeding either finite allowance.
