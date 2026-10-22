# The native polynomial and the exponential tail

Let K be the skew matrix of a real angular increment v, with q=|v|².
The identities `K³=-qK` and `K⁴=-qK²` show that the native small-angle
Rodrigues polynomial is exactly the matrix exponential series through degree
eight. The larger-angle expression is the exact exponential in ideal real
arithmetic. Neither identity establishes native floating-point accuracy.

Below the native binary64 threshold q₀=`1e-4`, the operator norm of K is at
most `sqrt(q₀)`. A rational upper endpoint is obtained by exact square checks.
Write a₀ for that endpoint and a₁,a₂,a₃ for bounds on the first three path
derivatives of v. If Eₘ(a₀) bounds the scalar exponential tail after degree m,
the differences between the two rotation expressions and their derivatives
are bounded by:

- `E₈`;
- `a₁ E₇`;
- `a₂ E₇ + a₁² E₆`;
- `a₃ E₇ + 3 a₁ a₂ E₆ + a₁³ E₅`.

The same bounds apply to one-sided changes at the switch for smooth input
paths. They count derivative placements in noncommuting matrix products and
bound each matrix entry by the operator norm. The tail is enclosed by its
first omitted term divided by `1-a₀/(m+2)`.

For an input range crossing the switch, the implementation encloses the true
exponential over the complete range, then enlarges each derivative interval
by the appropriate tail allowance. This contains both native branch expressions.
If the range lies entirely in the polynomial branch, the polynomial is
evaluated directly; if entirely in the other branch, no switch allowance is
needed inside that range.

Incoming argument changes must be handled separately. These local bounds do
not count every switch along a trajectory or propagate its effect through
subsequent steps. They also do not turn a piecewise formula into a globally
smooth one. The original motion adapter remains frozen and unchanged.
