# Bounds around the stated source reference row

The older prototype below is preserved for provenance. Its separate rounded
replacement passes the [six-source training qualification](../ilvis0-rounded-source-controls/INTERPRETATION.md)
and [all 24 native controls](../ilvis0-source-native-v2-controls/INTERPRETATION.md).
Complete prediction ranges are the next gate.

The prototype combines the verified training range for `A=R f` with a bound
for `B=R(P−I)f`, using the literal installation matrix's norm-defect allowance.
It converts the resulting coordinate intervals into error bounds around the
explicit source values and all 27 supplied coefficients.

Ten local tests pass. They cover all three model candidates and both processing
cases, retained training information, deliberately altered coefficient rows,
immutable certificates and reuse of a verified parent range on a smaller domain.
Contradictory intervals remain errors; they cannot become branch fallbacks.

For the first force term, the original remainder can be retained only after
including the exact known reference-center and row discrepancies. The body
term uses a fresh interval-to-affine error bound. It does not assume an old
Taylor radius belongs to a different row. This is conservative and can widen
some other-coordinate allowances, so complete usefulness must be measured.

The adapter is not yet installed or qualified in full native propagation. The
[compiled long-history screen](../ilvis0-compiled-range-preflight/INTERPRETATION.md)
now passes all six sources. A separate [point-domain check](POINT_DIAGNOSIS.md)
exposes an omitted reference-rounding allowance; its 18 expected failures are
preserved. The [rounding plan](ROUNDING_PLAN.md) records the replacement and
remaining integration work. No aircraft data was fitted.

The separate [physical source-value qualification](../ilvis0-source-value-controls/INTERPRETATION.md)
now passes all six sources. The new rounded adapter passes its training-transfer
and native qualifications too; the older expected failures above are preserved.

Implementation: `analysis/lll/ilvis0_body_interval.py`.
Tests: `analysis/tests/test_ilvis0_body_interval.py`.
