# Development evidence dataset

**53 selected stretches, 318 latest primary comparisons,
791 preserved numerical-history records, and 27 conservative split groups.**
The current numerical preference is 53 globe, zero flat and zero unresolved.
This snapshot does not report calibrated detections or a verified independent-flight count.

| Table | Contents |
|---|---|
| [Stretches](stretches.csv) | Source hashes, UTC bounds, selection, geometry, latest outcomes, gyro companion and validation fields. |
| [Latest primary comparisons](latest-primary-comparisons.csv) | All three models under both processing cases; kept separate from repeats and failures. |
| [Numerical history](numerical-history.csv.gz) | Every published history row, including 244 rows not marked converged. Some rows are diagnostics, not optimizer starts. |
| [Recording groups](recording-groups.csv) | Shared observations and unknown physical instrument/installation identities. |
| [Retained-file eligibility](retained-file-eligibility.csv) | All 232 files screened for this selected study, including nonqualifying files and aliases. |
| [Gyro baselines](gyro-baselines.csv) | The same observations beside three precomputed level/course predictions. |
| [Diagnostic studies](diagnostic-studies.csv) | Completed, failed and incomplete method studies, with their distinct scopes. |
| [Validation gates](validation-gates.csv) | Numerical completion, uncertainty, prediction and confirmation kept separate. |
| [Source index](source-index.csv) | Named input artifacts and SHA-256 hashes. |

## Scope and remaining work

An **IMU (inertial measurement unit)** records turning and specific force. Recorded
gyro increments are the turning observations; receiver positions locate the route.
The descriptive companion uses no fitted gyro correction or fused-attitude subtraction.

Original measurements, interval choices, failed results and blank hardware identities
are preserved. A history row ID identifies its place in this snapshot; it is not an
invented original worker identity. Repeated fits and overlapping recorders are not
independent replications. Source coordinate, calibration and processing assumptions
remain documented with their studies.

This is **development version 1**, not the final paper dataset. It covers the
53-stretch study and its retained-file selection, not a new 326-file acquisition
census. A complete acquisition-flow index and per-origin environment mapping remain
to be assembled. Earlier prediction outputs are indexed, not represented as qualified
held-out validation. Protected ESA records contribute reservation metadata only.
Withheld predictive adequacy, observational error assessment, independent confirmation
and calibrated dependence-aware decisions remain open.

The copied inputs, builder sources and outputs are immutable under this version.
The checker verifies frozen copies; an optional live-input check reports later
project changes without altering this snapshot. Building performs zero original
reads, model evaluations, optimizer starts or network requests.

`~/venv/bin/python docs/paper-development-dataset-v1/build_dataset.py --check`
checks the runtime and published snapshots. `--check-live` also checks the current
named project inputs. `--publish` only copies an already verified snapshot; it does
not rebuild tables or trigger analysis. A changed evidence set needs a new version.

[Selection criteria](ELIGIBILITY.md) · [Frozen assembly plan](PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
