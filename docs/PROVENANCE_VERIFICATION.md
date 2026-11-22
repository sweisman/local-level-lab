# Verifying the flight-group ledger

The published provenance ledger groups 53 selected airborne stretches into 27
conservative development groups. It also reserves seven ESA groups for later
confirmation. The grouping records shared evidence. Independence and shared
instrument installations require separate checks.

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

The [ESA forecast index](analysis-provenance/ESA_GROUP_EVIDENCE.md) separately
checks the receiver-row reuse in recording 187. It links the scored cuts to
one development group and retains the seven reserved groups in its receipt.
The [receiver screen](external-imu-data/ESA_CONFIRMATION_RECEIVER_INVENTORY_RESULT.md)
and [timing audit](external-imu-data/ESA_CONFIRMATION_TIMING_RESULT.md)
then verified one 20-minute slice in each reserved group. The group assignments
remain frozen, with all seven still awaiting confirmation fits.

[Published grouping](analysis-provenance/README.md) ·
[Development dataset](PAPER_DATASET.md) · [Study roadmap](ANALYSIS_ROADMAP.md).
