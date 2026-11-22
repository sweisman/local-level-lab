# Repository evidence and storage

## What uses the space

At the ESA confirmation-preparation release, the tracked tree contains
**10.08 GiB**. The reproduction archive takes **8.42 GiB** and the reports
and their evidence under `docs/` take **1.63 GiB**. The analysis directory
takes about **20 MiB**. A local checkout can also contain Git's stored objects,
downloaded observations, study journals and temporary work files.

Reproducing a single study needs its verified sources, inputs and evidence.
The [reproduction guide](REPRODUCIBILITY.md) shows how to verify and restore
that study by path. The current catalog refers to the archive packs by hash.
Moving the packs to other storage requires a retrieval and restoration check
before relying on the new location. Git retains older blobs in history even
after their paths leave the current checkout.

## Earlier pending evidence inventory

This snapshot records why the earlier local pending-file backlog existed.
It describes the state before the evidence batches were committed.

| Documented path | Pending files | Size of untracked files | Disposition |
|---|---:|---:|---|
| `repro/packs/` | 517 untracked | 6,915 MiB | Retain with the matching local archive catalog. |
| `docs/` | 565 untracked, 18 modified | 82.8 MiB | Review and publish coherent result groups. |
| `analysis/` | 266 untracked, 15 modified | 1.4 MiB | Review source and tests with the studies that use them. |
| `repro/` outside the packs | 2 modified | — | Review catalog changes together with their packs. |
| Root `README.md` | 1 modified | — | Review with the public status update. |

The scoped total is **1,384 pending files: 1,348 untracked and 36 modified**.
These counts come from a read-only Git status limited to the documented
`analysis`, `docs`, `data`, `repro`, `website` and named root project files;
they do not inventory unrelated workspace paths.

The local `repro/catalog.json.gz` at that checkpoint names **all 517 pending packs**.
Its path index points **351,735 archived paths** into those packs; none of
the 517 lacks a catalog path. Deleting a pack while retaining that catalog
would break hash-checked restoration. Committing the catalog without its
referenced packs would similarly break the public archive. The earlier
published catalog and packs remain a separate, internally consistent set.
The pending pack payload alone is about **6.8 GiB**, so it needs a deliberate
publication plan rather than one indiscriminate commit.

Most of the smaller pending files are source, tests, qualification records,
reports and portable study evidence. In particular, 433 untracked files
under `docs/prediction-observed-development/` occupy about 23.4 MiB, while
20 under `docs/esa-observed-model-dispatch-runtime/` occupy about 57.1 MiB.
These should be reviewed by logical study with their links and portable
dependencies before committing. An earlier byte comparison found 84 loose
runtime files duplicated exactly inside ten portable bundles, totaling only
about 0.88 MiB. They are possible cleanup candidates **after** each bundle
and all restoration dependencies are verified; removing them would barely
change disk use.
The ten single-file portable bundles together occupy about 36.5 MiB, so
they are not a replacement for the 6.8 GiB of cataloged pending packs.

No pending evidence was deleted, staged or committed in this inventory.
For study execution state, use the [canonical status command](../analysis/STATUS.md).
For archive verification and restoration, follow [Reproducing the studies](REPRODUCIBILITY.md).

## Reuse this inventory

The pending paths have already been classified. Use this map before repeating
an investigation of what the files are:

| Path pattern | Role | Next handling step |
|---|---|---|
| `analysis/lll/`, `analysis/tests/` | Shared study code, reports and focused controls | Review with the result documents that call them; keep historical source bindings intact. |
| `docs/<study>/` | Plans, qualification, receipts, public results and portable evidence | Check the study's completion record and receipt; publish a coherent study together. |
| `data/<study>/` | Local worker journals, charges and sealed results | Use `analysis/status.py` and the study verifier; never infer completion from a directory name. |
| `repro/catalog.json.gz`, `repro/catalog.json.sha256`, `repro/packs/` | One indexed, hash-checked archive | Treat catalog and newly referenced packs as one publication unit. Verify before any cleanup. |

An untracked pack is **not** an abandoned failed run: the local catalog
references every pack counted above. A failed numerical result is evidence and
must remain recoverable. A loose file may be removed only when its exact bytes
are verified in a retained archive and no active worker needs it. The 84 known
loose duplicates are small; they are not the source of the storage backlog.

The counts above describe the earlier audit, not live worker progress. New
studies can change them. For the next publication, start with the current
study index and completion records, then verify the catalog and packs as one
set. This avoids reclassifying hundreds of immutable pack names by hand.
