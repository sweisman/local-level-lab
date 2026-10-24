# Study status

From the repository root:

```sh
~/venv/bin/python analysis/status.py
```

This prints one line per study listed in `analysis/study-status.json`, including
completed results, passed numerical checks, errors, charged native calls, the
frozen call ceiling, allocated numerical threads and worker-lock state. Update
that small registry when a new study becomes current. It does not discover jobs
by scanning the repository or checking unrelated processes.

For machine-readable output or a particular runtime directory:

```sh
~/venv/bin/python analysis/status.py --json
~/venv/bin/python analysis/status.py --study data/ilvis0-profile-verification-20261017
```

The command reads existing metadata and takes only temporary, nonblocking lock
probes. It creates no study files, imports no numerical engines, reads no original
measurements and never launches, resumes, repairs or packages a study.

Completion records take precedence over stale progress snapshots after their
manifest and summary hashes are checked. While work is unfinished, known task
results supply progress and immutable receipt chains supply charged-call counts.
Workers that package their verified result inventory only at completion may also
publish an atomic `progress.json`. The command displays its bounded counts as a
separate **Worker snapshot**, never as verified passing results. Inconsistent
snapshot counts are rejected. Completed, hash-checked summaries remain authoritative.
Active native-call totals include separately journaled preflight checks as well
as fitting calls. Completion state may be explicit in either the completion
record or its hash-verified summary; an absent or unfinished state in both is rejected.
A charge is recorded before a native call; its presence does not mean the call
finished. A busy receipt ledger produces an explicit unavailable-snapshot warning.
Missing locks are never created. An unlocked, unfinished study is shown as
incomplete, even if its old status record says it was running.
An unfinished receipt transaction instead reports blocked continuation, retaining
the committed call count and preserving the incomplete files.

A completed study can still have a held lock while a dependent study reserves its
inputs. Lock ownership alone does not identify which process holds it. Thread
totals cover the monitored studies; they are not a machine-wide process inventory.
Passed checks describe the study's numerical checks, not scientific detections or
changes to the published globe/flat findings. `--json` includes failure reasons.

Long envelope batches can also show **Saved envelope reports**, counting the
hash-checked completed prefix at the fixed query times. This makes progress
visible before an entire case finishes. A saved report may precede a failed
acceptance check, so this count never becomes a passing result. The reader
creates or repairs nothing; an incomplete concurrent append is reported as an
unavailable snapshot. Each stream read is capped at 64 MiB. Completed studies
continue to use their sealed summaries.

Sharded controls also show charged bounds and their separate ceiling. Bound
reservations are checked against each shard's receipt chain; they are not
counted as native integration calls. Inherited shard leases retain the full
frozen thread reservation if the coordinator disconnects.

A hash-bound completed shard with a released lease cannot restart. Its thread
is subtracted from the active reservation, so a queued one-thread regression can
use that capacity without exceeding the four-thread total. Unfinished shards
retain their reservation.

The same registry can include `lll.studies.testing_after` runtime directories.
These show **waiting** with zero numerical threads, then **running** with one
thread after a completed shard releases its lease. The command checks the parent
manifest binding and completion/request hash, and counts the terminal XML test
results. A free queue lock without completion is incomplete, regardless of an
old snapshot. Test queues have no campaign-native-call counter; their test reports
remain separate from scientific attempt ledgers. Status inspection never starts
the queued tests itself.

Sequential suites can use `lll.studies.testing_chain`. It binds the predecessor
request, successor qualification and sources before waiting. The predecessor
must pass its required test count and release its lease before the next suite
can use that numerical core. Waits are finite; failed or changed evidence stops
the handoff, and a reserved chain cannot be retried.

Register the chain directory, rather than both the chain and its child queue,
to count its allocation once. Use one declared sequence for a released core;
independent queues must not compete for that same allocation. This schedules
local software tests only, and grants no scientific fitting allowance.

Exit status is zero for a readable snapshot, including completed studies with
recorded failures. It is nonzero for invalid or unavailable metadata, warnings,
or a monitored allocation above four threads. Unsupported historical metadata is
reported explicitly rather than guessed.
