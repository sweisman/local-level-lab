# Repository structure and storage

Most of the large file count came from repeated frozen code, copied inputs and
individual accounting receipts—not tens of thousands of different algorithms.
The first tracked-source inventory found **19,856 code files but 1,394 distinct
byte contents**. Different historical versions remain distinct.

| Tracked files in `docs` and `analysis` | Before | After |
|---|---:|---:|
| All files | 126,447 | 8,813 |
| Python/C/C++ source and headers | 19,856 | 1,487 |

These counts exclude local environments, original recordings and other ignored
files. The old versions remain recoverable from the evidence packs and Git history.

## What changed

Two verified migrations packed **125,266 published evidence files**, including
21,833 code files from frozen trees. Their expanded contents totaled about
**2.25 GB**; the shared packs total about **337 MB**. These figures cover the
migrated evidence, not the whole repository or original instrument archive.
Every migrated file was restored and compared before its expanded copy was
removed. Original measurements, results, failures and charges were preserved.

The local cleanup index identifies another **112,732 byte-identical copies**
in 177 completed study directories. It considers only declared public members
whose study manifest matches. Differing or unpublished files stay in place;
original instrument recordings are excluded.

| Location | Purpose |
|---|---|
| `analysis/lll` | Shared calculations, dataset adapters and analysis components. |
| `analysis/lll/studies` | Shared study lifecycle, accounting, evidence storage and publication tools. |
| `analysis/tests` | Deterministic checks and preserved historical entrypoints. New orchestration belongs in the shared library. |
| `docs` | Readable methods, study reports, figures, public tables and CSV downloads. |
| `repro` | Verified evidence packs, path/hash indexes and migration receipts. |
| `data` | Original recordings and local execution/cache state, kept separate from public evidence. |

New studies use a small definition and evaluator rather than another copied
launcher. The [reproducibility guide](REPRODUCIBILITY.md) describes the interface
and restoration commands. A CI check prevents adding more standalone study
command scripts under the test directory.

Git history retains the original trees. This reduces checkout file counts and
expanded storage; it does not rewrite or shrink existing Git history.

## What the timing checks show

Twelve fixed bookkeeping measurements compared generated 200-record fixtures.
Both implementations produced identical logical records and exports.

| Operation | Separate receipt files | Indexed journal |
|---|---:|---:|
| Append 200 charges | 4.89 s | 1.33 s |
| 100 count lookups | 1.46 s | 0.022 s |
| Export the audit records | 0.040 s | 0.019 s |

These are single engineering measurements, not general performance guarantees.
Individual archived result reads and complete archive verification were slower
than reading the small expanded fixture. Archives trade that cost for fewer
files and shared storage; indexed inventory lookup was faster.

No inertial calculation or physical bound changed. These bookkeeping gains do
not imply the same speedup for a long numerical analysis. The expensive
trajectory-bound calculations remain a separate optimization problem.

[Reproduce studies](REPRODUCIBILITY.md) · [Developer setup](DEVELOPMENT.md) ·
[Analysis roadmap](ANALYSIS_ROADMAP.md).
