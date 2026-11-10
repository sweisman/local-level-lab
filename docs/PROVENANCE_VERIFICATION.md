# Verifying the flight-group ledger

The published provenance ledger groups 53 selected airborne stretches into 27
conservative development groups. It also reserves seven ESA groups for later
confirmation. A group is not a verified independent flight or installation.

The ledger is a frozen input to the ESA selection study, so its original files
must remain unchanged. A later findings publication updated prose and source
bindings while retaining the two trajectory CSVs and the underlying findings
input hashes. The old ledger builder's exact `--check` therefore reports a
receipt mismatch in the current checkout. Regenerating the old ledger in place
would break the ESA study's source binding.

Use the separate read-only check instead:

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.provenance_snapshot_check
```

It verifies the archived findings receipt, both trajectory CSVs, the published
ledger and its receipt, and the grouping calculated from the saved metadata.
It also checks that the later findings receipt names the same underlying inputs
and trajectory CSVs. It reads no original IMU files and runs no fits. It does
not revalidate every artifact in the larger findings publication or turn the
conservative groups into independent replications.

[Published grouping](analysis-provenance/README.md) ·
[Development dataset](PAPER_DATASET.md) · [Study roadmap](ANALYSIS_ROADMAP.md).
