# Resuming the development continuation

The observed continuation is one separately charged task on ESA recording 187.
Its initial allowance is 2.5 million native calls, 10 billion packet visits,
four hours and one numerical thread. A reboot can interrupt that task, but
cannot erase its journal or turn its unfinished work into a completed result.

Run the same command after a normal start or after a reboot, from the repository
root:

```sh
~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- \
  ~/venv/bin/python -m lll.prediction_observed_continuation_resume --root .
```

The command checks the frozen study and its leases. If work is already owned,
it starts nothing. If the task is complete, it verifies the sealed result and
starts nothing. After an interrupted charged start, it seals the original
attempt, preserves its charge, and prepares at most one separately charged
recovery attempt with unchanged scientific inputs and method. A completed
numerical failure is retained, not retried. It sends no process signal.

The recovery uses the repository's task-level resume engine, qualified by
seven finite interruption tests. Three additional tests cover this command's
missing-study, completed-study and interrupted-study paths. The command is
idempotent, but it does not run automatically when the host is off; it must be
invoked again after a reboot unless a separate host service does so.

[Continuation plan](CONTINUATION_PLAN.md) · [Parent failure](DIAGNOSIS.md).
