# Bounds around the stated source reference row

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
[saved-baseline transport screen](../ilvis0-transport-range-preflight/PLAN.md)
and the [source integration plan](../ilvis0-source-stream-controls/NEXT_PLAN.md)
define the next gates. No aircraft data was fitted.

Implementation: `analysis/lll/ilvis0_body_interval.py`.
Tests: `analysis/tests/test_ilvis0_body_interval.py`.
