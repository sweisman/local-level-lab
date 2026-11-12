# Recovery for the fresh generated whole-period study

The frozen study is `data/prediction-simultaneous-law-family-v2-20261113`.
It is now closed. The separately qualified continuation completed the 12
previously unstarted tasks; four original deadline stops remain sealed failures.
The [audited result](RESULT.md) supersedes these launch instructions. Do not
run the commands below on this completed study.

## Historical recovery procedure

Keep its source, environment, inputs, charges, sealed failures and completed
results unchanged. Completed tasks never restart. An interrupted task can
receive a separately charged finite allowance only after the original study
is closed and no coordinator or shard lease remains owned.

After an interruption, inspect the durable state:

```bash
/home/sweisman/venv/bin/python analysis/status.py --study data/prediction-simultaneous-law-family-v2-20261113 --recovery
```

If active work remains, leave it alone. Otherwise close the original
allowance using the already qualified source-list repair:

```bash
PYTHONPATH=analysis /home/sweisman/venv/bin/python -m lll.studies.task_resume_sourcefix close-original --parent data/prediction-simultaneous-law-family-v2-20261113 --qualification-request docs/prediction-simultaneous-law-family-v2/qualification/recovery-request.json
```

Prepare **one** separate continuation if it does not exist:

```bash
PYTHONPATH=analysis /home/sweisman/venv/bin/python -m lll.studies.task_resume_sourcefix prepare --parent data/prediction-simultaneous-law-family-v2-20261113 --output data/prediction-simultaneous-law-family-v2-20261113-continuation --qualification-request docs/prediction-simultaneous-law-family-v2/qualification/recovery-request.json --max-attempts-per-task 4 --max-technical-interruptions 96 --maximum-wall-s 28800 --minimum-free-bytes 37580963840
```

Resume only unfinished identities through the numerical guard:

```bash
PYTHONPATH=analysis /home/sweisman/venv/bin/python analysis/tests/run_numerical.py --workers 4 --threads 1 --reserved-threads 0 -- /home/sweisman/venv/bin/python -m lll.studies.task_resume_sourcefix resume --output data/prediction-simultaneous-law-family-v2-20261113-continuation
```

The continuation checks source and environment hashes, receipts and leases
before scheduling. A lost notebook session is not permission to rerun sealed
tasks, reset charges or increase the original allowance.
