# Development evidence dataset: complete provenance indices

**All 326 catalog entries and all 791 numerical-history rows are now indexed.**
The original 53 selected stretches and their 53 globe / zero flat / zero unresolved
numerical preferences are unchanged. Version 1 remains sealed and independently checkable.

## Acquisition and selection

| Recorded pipeline disposition | Files |
|---|---:|
| Retained | 232 |
| Initial no-level rejections | 58 |
| Later no-level rejections | 35 |
| Verified duplicate removed | 1 |
| Unresolved final storage disposition | 0 |
| **Catalog total** | **326** |

The [catalog census](acquisition-census.csv) retains every URL, original-byte hash,
reported size, observed byte length, storage evidence and eligibility state.
The 232 retained sources contain 53 eligible stretches from 53 files; 179 retained
files have no stretch under the current four-minute/high-speed policy. Retention
does not itself mean scientific eligibility. Historical reference copies outside
the pipeline are outside this storage census. No file was opened, removed or
downloaded to produce the table.

## Numerical operation provenance

The [row index](numerical-origin-index.csv) links every history entry to its exact
publication record and execution manifest. [Sixteen origin labels](origin-summary.csv)
resolve to 23 execution manifests and
2 recorded numerical environments.
[Environment details](execution-environments.csv) preserve Python, NumPy, SciPy,
thread settings and kernel metadata from each operation, rather than using today's
environment or the environment of a later publication review.

There are 718 full-fit records,
10 conditional profiles and
63 endpoint-diagnostic records.
These are not independent trials. Failed and interrupted results retain their
original labels. The interrupted entry has no asserted evaluation count; its
reserved allowance remains visible. Diagnostics may reuse an earlier fitted point:
the direct source identity is preserved, but full point ancestry is not claimed
where it has not been reconstructed.

## Tables and interpretation

- [All 53 stretches](stretches.csv) and [318 latest primaries](latest-primary-comparisons.csv).
- [Complete numerical history](numerical-history.csv.gz), including failed records.
- [Conservative recording groups](recording-groups.csv) and [retained-file eligibility](retained-file-eligibility.csv).
- [Raw-gyro baselines](gyro-baselines.csv), [diagnostic studies](diagnostic-studies.csv), and [validation gates](validation-gates.csv).
- [Input hashes](source-index.csv), [selection criteria](ELIGIBILITY.md), and [assembly plan](PLAN.md).

An **IMU (inertial measurement unit)** records turning and specific force. Its
gyro increments supply turning observations; receiver positions supply route
context. Numerical preference, descriptive gyro agreement, predictive adequacy
and calibrated detection remain separate fields.

This is a development dataset, not the final validated paper dataset. The
27 conservative split groups are not verified independent flights. Qualified
withheld predictions, observational covariance, independent confirmation and
dependence-aware calibration remain open. Protected ESA measurements and model
outcomes were not read. No new fit, model evaluation or original-file read occurred.

Run `~/venv/bin/python docs/paper-development-dataset-v2/build_dataset.py --check`
to verify both versions and their frozen inputs. `--check-live` also checks named
current project inputs. `--publish` copies the completed snapshot without rebuilding
tables or running analysis. `--preflight` validates current metadata joins without
creating a snapshot. `--check-public` verifies the two public snapshots in a
repository checkout without any private runtime directory or original corpus.
Changed evidence requires a new version.

[Previous version](../paper-development-dataset-v1/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
