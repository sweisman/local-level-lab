# Next dataset revision: complete the provenance indices

**Completed in [development version 2](paper-development-dataset-v2/README.md).**
The design below records the metadata checks; it is not a pending execution queue.

Development version 1 is sealed. Its [checker](paper-development-dataset-v1/README.md)
must continue to verify; additions belong in a separately identified version.
This work uses saved metadata only, with no downloads, original-file decoding,
new fits or prediction evaluations.

## Link every numerical-history row to its origin

The 791 history records have sixteen published origin tags. Eleven embed their
source-study directory after `completed_`; their manifests are already indexed
by the current findings receipt. The five earlier aliases need explicit mappings:

| Origin label | Source stage |
|---|---|
| `original_first_pass` | All qualifying stretches: 318 original model/case attempts. |
| `qualified_subset` | Position-stability qualification: 24 attempts. |
| `completed_wider_recovery` | Full position recovery: 159 attempts. |
| `qualified_paired_precision` | Paired precision qualification: 16 attempts. |
| `completed_cost_precision` | Cost-precision recovery: 86 attempts. |

Preserve each original tag and worker identity. Join by source stage, role,
stretch, processing case, model and identity where available; do not invent a
worker identity for legacy blanks. Source manifests, completion hashes and
published results must substantiate the mapping. Conditional profiles and
fixed-endpoint checks retain their operation labels and cannot become full fits.

Record exact numerical environments, thread settings and source/kernel hashes
from each origin. Different freezes may legitimately use different allocations;
never assign the current environment retroactively. Missing evidence stays
explicit rather than being filled from a neighboring study.

## Reconcile acquisition and retention

Start from the 326-file catalog in the physical-validation catalog snapshot and
the named acquisition inventory in `data/ilvis0-ready`. Combine the documented
screening outcomes and duplicate-cleanup journal with the 232 retained-file
eligibility rows. Follow existing task IDs, filenames and stored hashes.

Every catalog entry needs one sourced final storage disposition and a separate
analysis-eligibility disposition. Retention, physical conversion, current
four-minute/high-speed eligibility and independent-flight identity are different
questions. Earlier counts of 233 originals remain historical; verified duplicate
removal explains the current 232. Do not delete or reacquire anything to build
this index. A missing hash or unresolved ledger relationship remains unknown.

## Verify and publish

Tests must reject ambiguous joins, changed hashes and mistaken operation classes,
preserve failed/interrupted rows, and keep all 53 selections unchanged. Reconcile
catalog, retained-source, selected-stretch and origin counts from the actual
ledgers before publishing a version 2 snapshot.

This metadata revision does not establish predictive adequacy, calibrated
uncertainty or independent replication. Those remain separate gates in the
[roadmap](ANALYSIS_ROADMAP.md).
