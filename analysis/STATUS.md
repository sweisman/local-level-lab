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

The command reads existing metadata and takes only temporary, nonblocking shared
locks. It creates no study files, imports no numerical engines, reads no original
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

Exit status is zero for a readable snapshot, including completed studies with
recorded failures. It is nonzero for invalid or unavailable metadata, warnings,
or a monitored allocation above four threads. Unsupported historical metadata is
reported explicitly rather than guessed.
