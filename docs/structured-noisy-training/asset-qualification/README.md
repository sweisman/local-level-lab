# Native build artifacts in reproducibility packages

All twelve metadata-only checks pass. The shared publication helper copies
only explicitly declared, hash-verified native assets from a completed study.
It rejects active studies, changed bytes, unexpected paths and duplicate entries.
No compilation, fitting or numerical libraries are used.

The [receipt](evidence-receipt.json) verifies 24 artifacts, including 22 source
snapshots. This is a reproducibility check, not an additional scientific result.

[Reproducibility guide](../../REPRODUCIBILITY.md) · [Running study](../README.md).
