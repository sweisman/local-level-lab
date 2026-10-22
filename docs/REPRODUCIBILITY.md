# Reproducing the studies

The public findings, flight tables, CSV downloads and figures remain ordinary
files. Detailed evidence and historical source snapshots are stored in compressed,
hash-checked packs inside this repository. Identical bytes are stored once,
even when many studies used them.

Packing changes storage, not the measurements or results. Original source bytes,
inputs, failures, resource charges and result hashes remain recoverable. The
original instrument recordings retain their separate acquisition and licensing
requirements; an evidence archive does not grant access to restricted data.

Run publication, migration and compaction commands one at a time. Wait for the
test runner to finish before changing its evidence workspace.

## Inspect, verify and restore

Use the existing Python environment from the repository root:

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies check
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies inspect docs/STUDY
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies restore docs/STUDY --destination data/reproduction
```

Replace `docs/STUDY` with the study directory shown in the [study index](STUDIES.md).
Restoration recreates the original relative paths and verifies their contents.
It refuses to overwrite a different file or follow a symlink outside the declared
destination. It performs no fitting or numerical simulation.

Historical commands may expect an expanded directory layout. Restore their
declared dependencies before running saved-result checks or report builders.
Run them using their frozen source and recorded numerical environment. A changed
Python, compiler, numerical library or algorithm is a new reproduction setting,
not an unchanged continuation.

The shared test command restores archived fixtures, runs the local suites and
compacts the restored copies after they finish:

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies test
```

Use `test --threads 2 --reserved-threads 2` when another job has a two-thread
allocation. A status record and lock under `data/study-test-runtime` preserve
the running test state. The runner never terminates a process to enforce time.
Test results are retained as an XML report. A test that runs for five minutes
prints diagnostic stacks without stopping the calculation.

Completed campaigns are never resumed. A new numerical reproduction needs a
new identity, finite limits and its own retained results; it cannot overwrite the
historical attempt ledger. Publication and verification commands perform no fits.

## How a new study is organized

A study has three small parts:

1. **Definition:** the question, preselected inputs, dependencies, task identities,
   acceptance checks, numerical environment and finite resource limits.
2. **Evaluator:** the calculation, calling shared components in the `lll` library.
3. **Report:** a brief explanation and tables drawn from sealed results.

The shared `lll.studies` interface handles preparation, execution, status,
accounting, verification, publication and archive restoration. The existing
bounded execution engine supplies worker locks, frozen dependencies, immutable
results and the four-thread total limit. New studies use a transactional indexed
charge journal; old receipt formats remain unchanged.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies prepare study-definition.json
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 4 -- ~/venv/bin/python -m lll.studies run data/STUDY --reserved-threads 0
```

The definition specifies the actual worker/thread allocation; the guard must
match it. Each study retains its own frozen allowance. Failed attempts stay charged.

An evaluator exposes `evaluate(task, context)`. The context supplies verified
inputs through `input_path()`, saves evidence through `save()`, and reserves
native work through `charge()` before execution. Its result includes a boolean
`passed` and a separate `scientific_decision`; software controls retain `abstain`.
The study plan and all numerical dependencies belong in the frozen source list.

Shared machinery replaces repeated launchers and boilerplate. Scientifically
different mathematical methods retain separate implementations and checks.
Historical studies continue to identify exactly which version they used.

## Storage and performance

The archive catalog maps original paths to SHA-256 hashes and immutable ZIP
packs. A complete verification checks both pack and individual-object hashes.
Migration restores and compares the original files before removing expanded
duplicates. Current public tables and downloads are kept outside the packs.

Performance changes are checked separately from scientific conclusions. Faster
journaling, dependency reuse or compilation caching must preserve accounting
and numerical results. A smaller repository does not improve the evidence by
itself, and faster calculations do not relax qualification requirements.

[Storage and timing results](REPOSITORY_STRUCTURE.md) · [Developer guide](DEVELOPMENT.md) · [Analysis roadmap](ANALYSIS_ROADMAP.md) ·
[Current findings](CURRENT_STATUS.md).
