# Development dataset revision 2: acquisition and execution lineage

Extend the sealed first snapshot without changing it or rerunning analysis.
All work uses named catalog, inventory, cleanup, selection and numerical-result
metadata. No downloads, deletions, original-file reads, native predictions or
optimizer starts occur.

## Acquisition census

Join every catalog item by task ID, filename and URL with the original 326-entry
inventory. Reconcile the 232 retained-file selection rows with the later no-level
cleanup journal and verified duplicate-removal journal. Prepared and removed
events must agree on source identity. A duplicate's canonical source must be
retained and have the same original-byte SHA-256.

Keep initial screening, recorded pipeline storage and current scientific
eligibility separate. Absence from the retained ledger is not deletion evidence.
Missing disposition evidence or hashes remain unknown. Preserve rounded catalog
sizes separately from observed original byte lengths. Supplied historical
reference copies outside the pipeline are not part of its storage census.

## Numerical lineage

Link all 791 published history rows to their exact publication record, retaining
blank legacy worker IDs, failed/interrupted outcomes and operation types. Validate
case/model/stretch/role identity, saved cost, convergence label and parameters.
Conditional profiles cannot become full fits. Interrupted evaluation counts remain
unasserted; their reserved allowance stays visible.

Trace execution manifests separately from publication-review manifests. A review
that reads saved results performs no fit and must not donate its environment to
the original operation. Use sealed result membership, declared tasks, charged
starts or preserved result envelopes to resolve ownership. Reject conflicting
owners rather than choose one by order or matching software versions.

Record exact Python/NumPy/SciPy versions, thread settings, source/kernel metadata
and manifest hashes. A diagnostic operation can reuse a previously fitted point;
preserve that source identity separately instead of treating the check as a new
fit. Unknown point ancestry or clock/calibration details stay unknown.

## Snapshot and gates

Build a separate immutable version with copies of all named input metadata and
builder sources. Preserve version 1 and verify both snapshots. Test identity
conflicts, ambiguous owners, tampered hashes, missing deletion evidence, unchanged
failure records and publication-versus-execution environment separation.

The original 53 selections and numerical preferences remain unchanged. A complete
metadata index does not establish withheld predictive adequacy, observational
covariance, independent replication or calibrated significance. Those remain
separate roadmap gates.

[Next-revision design](../PAPER_DATASET_NEXT.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
