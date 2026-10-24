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

Install the [development requirements](DEVELOPMENT.md) first. The suite also
uses the separately pinned website renderer to check links into archived evidence.

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

Long per-packet error propagation can use `TaskContext.prepay_native(...)`.
Reserve both native-call and packet-visit limits before entering the block;
call its `reserve(...)` before every native attempt. The block keeps unused
charges after interruption and checks cooperative stops at least every 128
attempts. Save its attempted-work snapshot after exit, before sealing the task.
Only new SQLite studies support this path. The
[accounting qualification](integrated-noise-covariance/prepaid-native-qualification/README.md)
checks status, merging and historical compatibility.

When compiled libraries are needed by a saved-results auditor, include their
declared source, binary and cache bindings in the publication receipt before
archiving. The [native-asset checks](structured-noisy-training/asset-qualification/README.md)
verify closed-study status and every selected byte without compiling or refitting.
The helper never searches for additional files.

Definitions can declare an explicit `scope`, which is included in the hashed
manifest. Receiver inventories and observed-data studies should describe their
actual purpose there. The historical default, “generated software controls
only,” remains available for generated controls. A scope label does not replace
input restrictions, qualification checks or a finite allowance.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies prepare study-definition.json
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 4 -- ~/venv/bin/python -m lll.studies run data/STUDY --reserved-threads 0
```

The definition specifies the actual worker/thread allocation; the guard must
match it. Each study retains its own frozen allowance. Failed attempts stay charged.

For new independent native-fit tasks, prefer several workers sharing the four
available numerical threads, with one thread per worker when memory permits.
The native integration loop is serial; giving it four BLAS threads does not
parallelize that loop. The [sharded execution checks](native-sharded-execution/README.md)
already verify one-thread native values and derivatives against the four-thread
reference. Bind and test the chosen environment before launch. Never change a
running or completed study's allocation to adopt this arrangement.

An evaluator exposes `evaluate(task, context)`. The context supplies verified
inputs through `input_path()`, saves evidence through `save()`, and reserves
native work through `charge()` before execution. Its result includes a boolean
`passed` and a separate `scientific_decision`; software controls retain `abstain`.
The study plan and all numerical dependencies belong in the frozen source list.
`save_bytes()` stores explicit binary artifacts with the same atomic writes,
owned-path checks and hashes as JSON evidence; it cannot overwrite an existing
artifact or write after its task is sealed. Generated numerical arrays can use
compressed NumPy archives without converting every value into JSON.

Tasks that mix value and derivative propagations declare `native_kind: mixed`.
Each native reservation then supplies `native_kind='value'` or `'tangent'`;
both consume the same frozen total-call and packet-visit allowance. Missing or
incompatible kinds are rejected before charging. Existing fixed-kind studies
retain their original behavior and cannot be reclassified.

Shared machinery replaces repeated launchers and boilerplate. Scientifically
different mathematical methods retain separate implementations and checks.
Historical studies continue to identify exactly which version they used.

When a numerical variant changes just one dependency, reuse the qualified
protocol instead of copying its worker. The [protocol-binding helper](../analysis/lll/studies/protocols.py)
checks the original source hash and substitutes exactly one declared imported
factory inside one function. All other statements remain unchanged. It compiles
only that function, records both syntax hashes and the provider's provenance,
and leaves the original module untouched. The wider-precision training adapter
uses this to preserve initialization, fit budgets, stopping checks, forecast
ordering and scoring while supplying its separately tested problem factory.
Binding checks alone do not qualify the provider's numerical behavior or the
resulting scientific procedure; those require matched controls and a new freeze.

New software qualifications can use `lll.studies.qualification` to write source
and environment bindings before a local test report exists. Its checker rejects
changed bindings, missing required tests, duplicate cases, failures and skips,
then returns the exact request/report bytes for the study freeze. Sixteen small
metadata controls pass. This checks test provenance; it does not establish
instrument accuracy, physical adequacy or statistical confidence.

The execution manifest also freezes the runner's shared files. Its source list
can therefore be larger than the calculation's preflight qualification list.
A saved-results audit checks that every qualified file is unchanged, that added
files belong to the shared execution machinery, and that every file in the full
manifest matches its frozen hash. The [shared source-binding check](../analysis/lll/studies/source_binding.py)
enforces that distinction; additional scientific code cannot enter through it.

## Storage and performance

The archive catalog maps original paths to SHA-256 hashes and immutable ZIP
packs. A complete verification checks both pack and individual-object hashes.
Routine packing and named compaction verify the catalog checksum, every affected
pack and object, alias sizes and expanded bytes. All selected targets are checked
before any expanded copy is removed. Unrelated historical objects are not scanned
again for each small update. The explicit `lll.studies check` command retains the
complete-store audit, including packs not used by that update.
The catalog is stored as deterministic `repro/catalog.json.gz`, with a SHA-256
checksum of the compressed file. The shared reader also accepts the earlier
uncompressed catalog; the next catalog write verifies and replaces that index
with its compressed equivalent. Evidence packs and original measurements stay
unchanged.
Migration restores and compares the original files before removing expanded
duplicates. Current public tables and downloads are kept outside the packs.

Performance changes are checked separately from scientific conclusions. Faster
journaling, dependency reuse or compilation caching must preserve accounting
and numerical results. A smaller repository does not improve the evidence by
itself, and faster calculations do not relax qualification requirements.

The native point-prediction kernels already integrate a history in one forward
pass and emit receiver predictions as their times are reached. They do not
restart the history for every receiver epoch. Each fit evaluation repeats that
pass for its proposed calibration; the derivative calculation also carries all
27 parameter directions through the history. The frozen packet/query work
allowance is a conservative accounting measure, not a count of nested loop
iterations or a wall-time estimate.

Further kernel changes need a separate equivalence and timing check. One
candidate is reusing the identical body-increment rotation calculations within
a midpoint step. Its speed benefit has not been measured. Such a change must
preserve values and every derivative, all three physical candidates, both
processing cases and both gravity treatments before a new observed-data freeze.
No running study adopts an optimization midway through execution.

Local software checks can also run in a declared sequence. Each handoff freezes
the previous request and successor sources, then checks the passing test report
and waits for the previous worker to release its allocation. Failed evidence stops
the handoff. This avoids overlapping suites without weakening a scientific
gate or launching a new fit. The [status command](../analysis/STATUS.md) reports
both waiting queues and their actual numerical allocation.

[Storage and timing results](REPOSITORY_STRUCTURE.md) · [Developer guide](DEVELOPMENT.md) · [Analysis roadmap](ANALYSIS_ROADMAP.md) ·
[Current findings](CURRENT_STATUS.md).
