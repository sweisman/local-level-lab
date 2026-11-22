# Independent-method study continuation

Both the generated control and the recorded-data pilot are complete. The
[recorded-data result](OBSERVED_METHOD_PILOT_V2_RESULT.md) has 7/24 numerical
stops and 4/6 matched path-agreement checks; the observed method did not
qualify. The commands below document the completed run and its interruption
procedure. They are not commands to restart either completed study.

The long generated control began with 24 frozen tasks. A host interruption
left 20 sealed completions, two charged unfinished tasks and two unstarted
tasks. The original allowance is now terminal. None of its completed fits may
run again. A separately qualified finite continuation completed the four
missing identities. The [saved-result report](LONG_INDEPENDENT_SOLVER_RESULT.md)
passed 24/24 stopping checks and all six generated-history gates. Read the
original and continuation stage states first:

```sh
~/venv/bin/python analysis/status.py --study data/ilvis0-long-independent-solver-v1-20261118
~/venv/bin/python analysis/status.py --study data/ilvis0-long-independent-solver-v1-20261118-recovery-v2/stage-000
```

An owned worker lease means a stage may still be running. Do not launch a
second coordinator or infer a dead worker from a sandboxed PID lookup. After
an interruption, use `--recovery` on the stage status command. The continuation
launcher checks the saved charges, seals, source hashes and leases, and assigns
only unfinished identities to a new finite stage:

```sh
~/venv/bin/python analysis/tests/run_numerical.py --workers 4 --threads 1 -- ~/venv/bin/python -m lll.studies.task_resume --project . resume --output data/ilvis0-long-independent-solver-v1-20261118-recovery-v2
```

The first continuation preparation exposed a duplicate source-name check and
charged no tasks. The repair passed the six reboot/charge tests and was frozen
as `recovery-v2`. The original study's frozen code and results remain intact.
The saved-result report combines the 20 original completions with the four
recovered identities and rejects duplicate or missing results. It can be
reproduced without fitting again:

```sh
~/venv/bin/python -m lll.ilvis0_long_independent_solver_report
```

Only a sealed result that passes the separate six-fixture report gate permits
the observed development pilot. Its earlier one-task SciPy preflight was
prepared but never charged. The recovery-launcher repair changed a source
bound by that preparation, so a [new versioned plan](OBSERVED_METHOD_PILOT_V2_PLAN.md)
and 15 passing source tests were prepared. Refresh their source-hash binding
after the long report is finalized. Keep the old preparation intact and do
not run its stale commands. The new study's own preparation checks the
generated gate before opening any recorded input.

The [one-task observed SciPy preflight](OBSERVED_METHOD_V2_PREFLIGHT.md)
passed its wiring check. Its 30-call fit did not converge, so it is not a
scientific fit qualification. Its original commands were:

```sh
~/venv/bin/python -m lll.ilvis0_observed_method_pilot_v2 prepare-preflight
~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.ilvis0_observed_method_pilot_v2 run-preflight
```

Then prepare and run the versioned 24-fit observed study under four one-thread
workers. Inspect its status and recovery evidence after any interruption.
Never enlarge an allowance or restart a sealed fit. The original 80 observed
fit labels remain unchanged.

```sh
~/venv/bin/python -m lll.ilvis0_observed_method_pilot_v2 prepare
~/venv/bin/python analysis/tests/run_numerical.py --workers 4 --threads 1 -- ~/venv/bin/python -m lll.ilvis0_observed_method_pilot_v2 run
```

If the host stops during the 24-fit study, first inspect its `--recovery`
status and confirm no coordinator or shard lease is owned. A charged unfinished
fit cannot be restarted in the original allowance. Seal that allowance, then
prepare a separately qualified finite task continuation. These commands are
for an actual interruption only; a completed original study cannot restart.

```sh
~/venv/bin/python analysis/status.py --recovery --study data/ilvis0-observed-method-pilot-v2-20261118
~/venv/bin/python -m lll.studies.task_resume --project . close-original --parent data/ilvis0-observed-method-pilot-v2-20261118 --qualification-request docs/prediction-group-transfer/long-independent-recovery-repair-request.json
~/venv/bin/python -m lll.studies.task_resume --project . prepare --parent data/ilvis0-observed-method-pilot-v2-20261118 --output data/ilvis0-observed-method-pilot-v2-20261118-recovery --qualification-request docs/prediction-group-transfer/long-independent-recovery-repair-request.json --max-attempts-per-task 3 --max-technical-interruptions 24 --maximum-wall-s 21600 --minimum-free-bytes 21474836480
~/venv/bin/python analysis/tests/run_numerical.py --workers 4 --threads 1 -- ~/venv/bin/python -m lll.studies.task_resume --project . resume --output data/ilvis0-observed-method-pilot-v2-20261118-recovery
```

The continuation reuses every sealed outcome, including failures. If it is
itself interrupted, run its `resume` command after verifying leases and hashes;
the finite attempt and wall limits still apply. The versioned saved-result
report accepts a complete original study or a verified completed continuation.
