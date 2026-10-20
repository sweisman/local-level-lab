# Body rotation and force: the next adapter check

Component integration is not enough when the rotation axis changes. This
prerequisite compares mean-rate midpoint increments with an independently
integrated body-frame differential equation. It does not fit an aircraft or
assume an Earth-rate target.

For one interval of length `h`, suppose angular rate and specific force are
linear between their two reported point samples. Define their means `w`, `f`,
angular-rate slope `b`, force slope `d`, and maximum endpoint force norm `F`.
The midpoint approximation uses `exp(skew(w)*h)` and
`exp(skew(w)*h/2)*f*h`. These are exactly the body-only operations that the
constructed midpoint increments imply.

An operator-norm bound for the rotation discrepancy is

\[
e_R\leq\min\left(2,\;\|w\times b\|h^3/12+\|b\|^2h^4/32\right).
\]

To obtain it, factor out the constant mean rotation. The remaining generator
is `(t-h/2)` times a rotated `skew(b)`. Its fixed midpoint contribution
integrates to zero; the changing conjugation contributes at most the commutator
term above. The second-order integral remainder is bounded by half the squared
integral generator norm, giving `||b||²*h⁴/32`. Exact rotations have discrepancy
at most two. No assumption about small angle is needed for this mathematical bound.

The corresponding body-force integral discrepancy is bounded by

\[
e_F\leq \|b\|Fh^3/8+
\left(\|w\|^2F+2\|w\|\|d\|\right)h^3/24.
\]

The first term integrates the variation-of-constants rotation bound against
force. The second is the midpoint quadrature bound for a constant mean rotation
acting on linear force. This is a local body calculation: geographic transport,
gravity, Coriolis, antenna motion and cross-interval accumulation are separate.

Tests must compare changing-axis and changing-force paths with an independent
matrix/force ODE solution, as well as exact constant and zero-rate cases. A
finite generated study must freeze cases and work limits before execution.
Keep all existing sources and studies unchanged.

These bounds assume linear **point samples**. They do not identify the actual
instrument's averaging, filtering or sampling phase. They are mathematical
approximation bounds, not a complete floating-point enclosure or calibrated
observational uncertainty. No protected data or archive fits enter the check.

[Component adapter](README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
