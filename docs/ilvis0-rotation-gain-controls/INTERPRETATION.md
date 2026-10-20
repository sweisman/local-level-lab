# Force-matrix support constraints pass their controls

All 24 generated controls passed in 4.64 seconds. They checked 1,536 physical
probes and 119,808 new rotation/gain inequalities. The reused independent
Rodrigues/force oracle also repeats its existing vector-norm validations;
those are separate from the new inequality count. Its maximum difference
from the supplied component was 1.42 × 10⁻¹⁵.

A rotation changes a vector's direction without stretching it. Calibration
gains supply a known, bounded scale change. The new constraints preserve
necessary consequences of those facts for the shared force matrix, including
gain dependence. They use exact reciprocal chords and outward coefficient
exports. No future observation chooses a constraint direction.

The local tests also reject an outward matrix stretch that remains inside the
earlier error-vector balls. Point domains preserve the existing zero-error
normalization. All 51 coordinates and the original physical bounds remain.

This is a component qualification, with no original-file reads or native
integration. The [saved-case comparison](../ilvis0-rotation-gain-prediction/PLAN.md)
separately tests usefulness. Neither calculation establishes aircraft error
coverage or a whole-program floating-point certificate.

[Results](README.md) · [Frozen derivation and limits](PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
