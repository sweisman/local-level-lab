# Native-control sharding plan

## Goal and boundaries

Run future native qualifications and generated prediction studies with up to
four independent workers, one numerical thread each. Preserve the physical
calculations, deterministic inputs, immutable task identities, finite allowances
and failure records. Completed and active studies keep their original runners
and allocations. This plan adds execution infrastructure; it does not permit
new observed fits, relaxed scientific gates or protected ESA evaluation.

The existing campaign runner targets a different synthetic-flight format and
remains unchanged. Reuse its generic file-lock/write principles and the existing
immutable receipt ledger, without changing either frozen implementation.

## Files and interfaces

- `analysis/lll/ilvis0_control_shards.py`: standard-library planning, source/input
  freeze, task charging, shard execution and checked merging.
- `analysis/tests/ilvis0_control_shards.py`: coordinator/worker command entry;
  numerical environment is set before importing a scientific adapter.
- `analysis/tests/test_ilvis0_control_shards.py`: deterministic standard-library
  bookkeeping controls, followed by bounded process lifecycle controls.
- `analysis/status.py`: recognize active shard leases even if a coordinator has
  disconnected; keep the existing generic status command.
- A separate native adapter and finite qualification are added only after the
  execution controls pass. Numerical compatibility at one thread must be tested
  before a longer parallel prediction study.

## 1. Immutable storage and charge scope

- [x] Define `prepare(output, project_root, tasks, sources, inputs, adapter,
  workers, threads, maximum_wall_s, environment)`; validate the four-thread
  allocation, unique safe identities, nonnegative finite per-task limits and
  explicit source/input paths before writing a new manifest.
- [x] Copy only those explicit sources and inputs into the new study. Reject
  paths escaping their declared root, source/input changes and existing output
  freezes. The manifest binds task ordering, assignment (`index % workers`),
  sources, environment and every resource limit.
- [x] Define `TaskContext(study, shard, identity)` with `charge(**resources)` and
  `save(name, value)`. Each task start is charged before its adapter runs;
  native and bound operations are charged before execution. Interrupted starts
  remain charged and are never retried.
- [x] Use one immutable receipt chain per shard. Exact native/bound counters and
  packet reservations are checked against each task's own limits. The existing
  ledger's internal phase names do not imply new statistical fits.
- [x] Define `merge(study)` to verify sources, inputs, receipts, expected shard
  assignment, unique identities, result hashes, side artifacts and resource
  totals. Merging never runs an adapter. Missing and interrupted identities stay
  explicit; a completed execution is not by itself scientific qualification.

Initial tests use standard-library fixtures only:

```sh
~/venv/bin/python -m unittest analysis.tests.test_ilvis0_control_shards -q
```

Require rejection of duplicate identities, out-of-domain charges, changed input,
changed result, duplicate/wrong-shard results, an incomplete charge transaction
and a second start of an already charged identity. A failed write must never
turn charged work back into an unused allowance.

The first eight standard-library storage controls pass. Numerical execution and
process qualification remain the separate next stages below.

## 2. Process ownership and continuation

- [x] Define `run_shard(study, shard, evaluate, lease_fd=None)` and
  `launch(study, reserved_threads=0)`. Apply the frozen numerical environment
  before numerical imports. Check the actual reserved allocation before launch.
- [x] Acquire each shard lease before spawning its child and pass that locked
  file descriptor with `pass_fds`. The parent closes its copy without unlocking
  it. This removes the gap in which a child exists but has not acquired its lock.
- [x] Start children in independent sessions and preserve logs/metadata.
  A coordinator disconnect must not kill numerical work. Never call terminate,
  kill or send a process signal.
- [x] On continuation, refuse to duplicate any held shard lease. Once all old
  leases are free, keep sealed results, mark charged unfinished identities as
  interrupted, and execute only previously uncharged identities within the
  original deadline. Never repair a corrupt receipt or extend an allowance.
- [x] Cooperative deadline/failure requests prevent new charged operations;
  running operations finish under their own frozen limits. Preserve the first
  failure and all concurrent charges. Use a declared stop policy, not ad hoc
  retries or favorable-case selection.

Process controls cover inherited lease ownership, coordinator loss, duplicate
launch rejection, interrupted work, a changed environment, deadline exhaustion,
side-artifact corruption and bitwise-stable known-answer output under different
completion order. No numerical child is launched while another four-thread
study occupies the allocation.

The process implementation and status adapter pass mocked controls. Real process
qualification is separately bounded in [the qualification scope](QUALIFICATION.md).

## 3. Qualification before scientific use

- [x] Implement preparation of a finite execution-control study with explicit task/event limits,
  zero observed starts and zero native integration calls. Its intentional
  lifecycle failures test the runner; they are not scientific outcomes.
- [x] Freeze, execute and verify the nineteen controls, including twelve real
  fixture-worker starts, after the numerical allocation is free.
- [x] Add an adapter around the unchanged qualified native-control calculations.
  New data paths, charging and publication are isolated from completed studies.
- [x] Freeze a separate one-thread-per-worker native qualification, matching the
  original generated inputs and comparison limits. Compare scientific values,
  Jacobians and factored bounds with the preserved four-thread reference.
- [x] Only after both gates pass, freeze a new longer prediction comparison.
  Keep its source, environment, task/resource/deadline limits and assignment
  immutable. No existing serial study is converted or relaunched.

Public reports separate software execution, native mathematical correctness,
prediction usefulness and observational coverage. No automatic production
decision or evidence promotion follows from parallel execution.

[Roadmap](../ANALYSIS_ROADMAP.md) · [Status guide](../../analysis/STATUS.md).
