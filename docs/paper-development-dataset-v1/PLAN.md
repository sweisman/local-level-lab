# Development evidence dataset, version 1

Assemble an immutable metadata snapshot of the 53-stretch study. This is an
incremental paper dataset, not the final validated dataset or an independent
replication. No measurements, selections, numerical results or thresholds change.

## Contents

- All 53 selected stretches, original file hashes, UTC bounds, geometry,
  configuration, selection version, current numerical preference and explicit
  validation gates.
- All 318 latest model/processing-case primary comparisons, separately from the
  published numerical history, including failed and interrupted records.
- Conservative split groups and shared-leg identifiers, preserving unknown
  physical instrument and installation identities as unknown.
- The 232-file eligibility ledger for the retained study pool, including
  nonqualifying files and aliases. Earlier archive-acquisition exclusions remain
  in their separate ledgers; this is not a new 326-file acquisition census.
- All 159 raw-gyro baseline comparisons and their declared assumptions; the
  full fixed-scenario archive is indexed separately.
- A source/evidence index with SHA-256 hashes, including completed, failed and
  incomplete prediction-method studies. Protected ESA membership is metadata
  only; no protected measurements or model outcomes are read.

## Integrity and interpretation

Verify source receipts before joining. Require matching stretch sets, source
hashes, configuration and selection identities. Every latest comparison must
retain all three models and both processing cases. Preserve every history row,
even blank legacy attempt identities; assign a separate snapshot row ID without
claiming it is the original worker identity. Never substitute a repeat for a primary.

Keep numerical preference, descriptive agreement, predictive adequacy, calibrated
uncertainty and independent replication in separate fields. The dataset reports
no calibrated detections, confidence levels or verified independent-flight count.
Do not infer hardware identity from type/configuration bytes. Missing prediction
qualification remains missing; earlier development predictions stay indexed.

Build once from named documented inputs. Freeze copied inputs, builder/module
sources and generated outputs under this version. A read-only check verifies
the frozen snapshot; later changes to live project pages cannot rewrite it.
An optional live-input check may identify drift without repairing or regenerating
the snapshot. Changed evidence needs a separately identified version.

This metadata-only build performs zero original reads, model evaluations, optimizer
starts or network calls. It does not need a new observed-data campaign allowance.
The final paper dataset remains gated on withheld prediction, observational error
assessment, independent confirmation and dependence-aware calibration.

[Roadmap](../ANALYSIS_ROADMAP.md) · [Current findings](../CURRENT_STATUS.md).
