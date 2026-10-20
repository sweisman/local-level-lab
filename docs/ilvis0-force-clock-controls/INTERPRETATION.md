# One common clock is retained through the force integrals

All **24 component controls pass**, covering 288 parameter probes, 1,296
finite-step derivative evaluations and 1,728 exact rational integral inequalities.
Independent suffix-weight quadrature checks the centres; independent rotation
and gain calculations check the matrix-weighted result.

The construction preserves a single time offset across all packets. It also
retains packet-tag defects, matrix/clock cross terms and rounding when exact
coefficients are exported as binary floats. Point-clock controls produce no
manufactured variable-clock remainder. All 27 physical directions and the
51-column design remain.

The calculation used 270 independent history queries and 219,840 combined
integral/oracle packet visits, within its frozen limits. No native integration
calls, original aircraft reads or observed fits occurred.

The next gate is native propagation. Its midpoint cancellation must preserve
the original dynamics before a typed 51-column training/prediction interface
or another complete prediction comparison can follow. Recording-scale usefulness,
whole-program numerical treatment and actual observation-error adequacy remain
open. The 53-stretch empirical findings are unchanged.

[Qualification evidence](README.md) ·
[Native derivation](../ilvis0-common-force-transform/NATIVE_PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
