# Shared observations and protected confirmation data

The 53 selected archive stretches form **27 conservative split groups**. These groups keep same-date observations, byte aliases, overlapping intervals and candidate shared legs together. They are not 27 verified independent flights or installations.

The nine cataloged ESA files form **8 conservative date/file groups**: one development group (recording 187) and **7 protected confirmation groups**. Reported flight labels sharing a file stay together. Model outcomes from protected groups remain unexamined.

[Every recording/stretch](recording-groups.csv) · [Every split group](groups.csv) · [Complete relationship graph](ledger.json) · [Execution roadmap](../ANALYSIS_ROADMAP.md).

## What is known and what is grouped conservatively

Source hashes identify byte aliases; UTC intervals identify temporal overlap. Saved shared-leg matches remain candidate same-track relationships. Same-date grouping is a deliberate protection against leakage, not proof of one aircraft. Physical instrument and installation identities remain unknown; matching configuration bytes do not fill those fields. Separate dates may still share hardware and systematic errors.

Different groups are therefore units for conservative development splits, not a measured number of independent replications. Later evidence may merge groups; any split-policy change needs a new version before evaluation.

## ESA reservation

Use recording 187 for development. The other eight currently cataloged files are protected confirmation material. Integrity, inventory and receiver-only eligibility checks are allowed. Model fitting and model-outcome inspection wait until selection, method, uncertainty, adequacy rules and confirmation identities are frozen. A new or unassigned file is not development data by default.

The metadata helper rejects development/confirmation membership in a shared group and exposes a development-only guard for future workers. No model worker is launched by this ledger; confirmation authorization must be implemented and checked in its separately frozen worker.

The original 53 intervals, measurements and dispositions are unchanged. The NASA corpus has already informed method development; new blocked predictions are retrospective validation rather than untouched confirmation.

## Reproducibility

Run `~/venv/bin/python docs/analysis-provenance/build_ledger.py` to regenerate, or append `--check` for a read-only consistency check. The builder reads only named saved metadata, verifies the source findings hashes, and performs no original-file reads, integrations, fits or network requests. Input and output hashes are recorded in the receipt.

[ESA source inventory](../external-imu-data/README.md) · [Findings](../CURRENT_STATUS.md).
