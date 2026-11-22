# Execution and recovery check

The source, input and environment freeze contains 232 file tasks, one worker,
one numerical thread, a four-hour wall limit and zero model evaluations.
The prepared manifest is SHA-256
`88dad963e6102ad02ec4299dc6245e2ca22069fb49b9097d20c37d80fecf8aa2`.

The focused selector/adapter checks and shared worker/task-continuation
recovery checks passed 44/44 with one numerical thread. Interrupted starts
retain their charges and sealed results are not repeated. The original run
resumes only tasks that were never started; a separately charged continuation
is required to recover an interrupted task. The idempotent resume entry point
verifies the original manifest and journals before scheduling work:

```sh
~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- \
  ~/venv/bin/python -m lll.studies run data/ilvis0-receiver-raw-inventory-20261116 \
  --reserved-threads 0
```
