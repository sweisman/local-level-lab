# Carry direction through the calculation

The previous static-bound replacement did not improve complete predictions.
The next component keeps separate horizontal and vertical bounds as values move
through the calculation. It does not discard the tighter training-derived
information already available.

The prototype now supports vector and matrix arithmetic, matrix actions,
scalar reciprocals and square roots. It keeps separate coordinate-change and
reference-linearization error bounds. Operations use exact rational bound
arithmetic, outward export and explicit reference-value rounding allowances.
Singular or ambiguous domains are rejected.

Forty local tests cover exact polynomial curves, matrix actions,
rounding, immutable inputs, source-prefix support and rotation controls. A separate rotation-length
identity can tighten vertical departure when the learned force direction is
known. Its norm and linearization premises must be established from the source;
an interval box alone cannot prove them. These are mathematical controls, not
aircraft findings or measurements of the cause of the current prediction widths.

## What remains

The [six-source preflight](../ilvis0-source-norm-preflight/INTERPRETATION.md)
now passes against the actual saved source and its training-conditioned bounds.
A value-range improvement is insufficient for
replacing a Taylor remainder: all reference coefficients must agree or their
differences must be bounded explicitly. Rotation updates, inverse-skew
operations, time and lever-arm terms also need compatible bounds. Preserve
every physical/shared-error column and test improvement against the actual
baseline before another complete comparison.

The prototype is separate from all frozen engines. It has not produced new
aircraft fits or qualified full-recording prediction ranges.

[Implementation](../../analysis/lll/ilvis0_directional_values.py) ·
[Operator derivation](OPERATOR_DERIVATION.md) ·
[Matrix operations](../../analysis/lll/ilvis0_directional_matrices.py) ·
[Scalar and rotation identity](../../analysis/lll/ilvis0_directional_scalar.py) ·
[Tests](../../analysis/tests/test_ilvis0_directional_values.py) ·
[Previous diagnosis](../ilvis0-directional-prediction/BASELINE_DIAGNOSIS.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
