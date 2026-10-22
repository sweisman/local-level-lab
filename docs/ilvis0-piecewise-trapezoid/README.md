# Accounting for clock boundaries in approximation error

An exact-arithmetic component now encloses the endpoint-average error when
derivative bounds and boundary-jump bounds are supplied. It does not silently
treat missing jump information as zero. Unsupported jumps in the residual
itself are rejected.

Fourteen focused checks cover smooth examples, derivative steps and hinges,
an independently integrated piecewise quadratic, outward endpoints and
incomplete or invalid bounds. The result keeps native clock coverage and
native derivative bounds explicitly unverified.

This supplies one mathematical part of the next prediction bound. The native
calculation must still provide valid derivative and jump bounds over its whole
declared parameter/clock region. No new integration or aircraft fit was run.

[Mathematical identity](MATHEMATICS.md) · [Source](../../analysis/lll/ilvis0_piecewise_trapezoid.py) ·
[Tests](../../analysis/tests/test_ilvis0_piecewise_trapezoid.py) · [Current work](../NEXT_STEPS.md)
