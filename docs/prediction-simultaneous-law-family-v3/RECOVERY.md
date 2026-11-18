# Recovery procedure for the generated cohort

This procedure was used after the original launch was interrupted. Its
source-bound recovery qualification and short frozen-worker preflight passed
before launch. The continuation has closed; the [saved-result audit](RESULT.md)
verified all 96 tasks and the frozen generated-data gate passed. The commands
below are retained to document recovery, not to repeat completed work.

The study ID is `prediction-simultaneous-law-family-v3-runtime-20261112`.
After a reboot, first inspect its saved state and leases:

```bash
/home/sweisman/venv/bin/python analysis/status.py --study data/prediction-simultaneous-law-family-v3-runtime-20261112 --recovery
```

If an authorized worker is active, leave it running. If the original allowance
is closed and tasks never started or were interrupted, use the qualified
versioned recovery command. It verifies source and environment hashes, charges,
receipts and leases. It must never repeat a sealed success or failure.

```bash
PYTHONPATH=analysis /home/sweisman/venv/bin/python -m lll.studies.task_resume_sourcefix close-original --parent data/prediction-simultaneous-law-family-v3-runtime-20261112 --qualification-request docs/prediction-simultaneous-law-family-v3/qualification/recovery-request.json
```

Prepare one separate, finite continuation only if it does not already exist:

```bash
PYTHONPATH=analysis /home/sweisman/venv/bin/python -m lll.studies.task_resume_sourcefix prepare --parent data/prediction-simultaneous-law-family-v3-runtime-20261112 --output data/prediction-simultaneous-law-family-v3-runtime-20261112-continuation --qualification-request docs/prediction-simultaneous-law-family-v3/qualification/recovery-request.json --max-attempts-per-task 4 --max-technical-interruptions 96 --maximum-wall-s 43200 --minimum-free-bytes 37580963840
```

Resume only its unfinished identities through the four-thread guard:

```bash
PYTHONPATH=analysis /home/sweisman/venv/bin/python analysis/tests/run_numerical.py --workers 4 --threads 1 --reserved-threads 0 -- /home/sweisman/venv/bin/python -m lll.studies.task_resume_sourcefix resume --output data/prediction-simultaneous-law-family-v3-runtime-20261112-continuation
```

The continuation has a separate charge and cannot increase the original
12-hour allowance. Any sealed technical failure remains a failure in the final
96-recording gate.

After all tasks have sealed, publish from saved evidence without fitting:

```bash
PYTHONPATH=analysis /home/sweisman/venv/bin/python -m lll.prediction_simultaneous_report_v3
```

The publisher verifies completion receipts, frozen sources, task identities
and both withheld-target scores before writing the result and per-recording
ledgers. Run it only after closure, including any qualified continuation.
