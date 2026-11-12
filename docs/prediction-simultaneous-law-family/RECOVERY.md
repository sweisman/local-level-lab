# Recovery for the generated whole-period study

The frozen study is `data/prediction-simultaneous-law-family-v1-20261112`.
The original 96 tasks, source and environment hashes, charges and sealed
results must remain unchanged. Completed failures count as outcomes; only
technically unfinished work may receive a new, separately charged allowance.

After a notebook interruption, first run:

```bash
/home/sweisman/venv/bin/python analysis/status.py --study data/prediction-simultaneous-law-family-v1-20261112 --recovery
```

If any coordinator or shard lease is owned, leave it alone. Once no worker is
active, close the original allowance, preserving charged interruptions:

```bash
PYTHONPATH=analysis /home/sweisman/venv/bin/python -m lll.studies.task_resume_sourcefix close-original --parent data/prediction-simultaneous-law-family-v1-20261112 --qualification-request docs/prediction-simultaneous-law-family/qualification/recovery-request.json
```

Prepare the separate continuation **once** if its directory does not exist:

```bash
PYTHONPATH=analysis /home/sweisman/venv/bin/python -m lll.studies.task_resume_sourcefix prepare --parent data/prediction-simultaneous-law-family-v1-20261112 --output data/prediction-simultaneous-law-family-v1-20261112-continuation --qualification-request docs/prediction-simultaneous-law-family/qualification/recovery-request.json --max-attempts-per-task 4 --max-technical-interruptions 96 --maximum-wall-s 28800 --minimum-free-bytes 37580963840
```

This final command is idempotent across further interruptions. It rechecks the
frozen sources, numerical environment, prior charges, result seals, ownership
leases and finite limits before scheduling only unfinished task identities:

```bash
PYTHONPATH=analysis /home/sweisman/venv/bin/python analysis/tests/run_numerical.py --workers 4 --threads 1 --reserved-threads 0 -- /home/sweisman/venv/bin/python -m lll.studies.task_resume_sourcefix resume --output data/prediction-simultaneous-law-family-v1-20261112-continuation
```

All commands use the qualified source-list repair. No original sealed result
is restarted, and neither the original nor continuation allowance is expanded.
