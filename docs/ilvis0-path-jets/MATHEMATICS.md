# Third-order interval arithmetic

`analysis/lll/ilvis0_path_jets.py` stores actual derivatives of orders 0–3,
not Taylor coefficients divided by factorials. Each input interval must contain
the corresponding derivative throughout the declared path. Arithmetic uses
rational endpoints; published floating endpoints round outward.

Products use the binomial Leibniz rule. Reciprocal derivatives follow by
differentiating `a*q = 1`: `q[0] = 1/a[0]` and
`q[n] = -q[0] * sum(comb(n,k)*a[k]*q[n-k], k=1..n)`.
An interval containing zero is rejected before inversion. Interval dependency
can widen an enclosure; it does not make the enclosure narrower than justified.

For `K = skew(v)`, the rotation is enclosed by the matrix series through degree
N. Let `a[j]` bound the Euclidean norm of the jth derivative of v, and let
`E[m](a[0])` bound the scalar exponential tail after degree m. The entrywise
tail allowances for derivative orders 0–3 are:

- `E[N]`;
- `a[1]*E[N-1]`;
- `a[2]*E[N-1] + a[1]^2*E[N-2]`;
- `a[3]*E[N-1] + 3*a[1]*a[2]*E[N-2] + a[1]^3*E[N-3]`.

These follow by counting all derivative placements in each matrix product;
they do not require commuting matrices. The scalar tail is bounded by its
first omitted term divided by `1-a[0]/(m+2)`. Supported degrees are 12–48 and
the argument norm is at most eight, ensuring that denominator is positive.

Real skew matrices have orthogonal exponentials. The integral formula for
each Frechet derivative bounds its operator norm by the product of the
direction norms: every intervening exponential has norm one. The chain rule
therefore gives rotation derivative norm bounds
`1`, `a[1]`, `a[2]+a[1]^2`, and
`a[3]+3*a[1]*a[2]+a[1]^3`.
Intersecting the series enclosure with these entrywise norm bounds is valid.

Tests independently check rational scalar derivatives, calibration convention,
a noncommuting zero-angle example and nonzero-angle sine/cosine series.
They do not establish a complete native clock partition, trajectory derivative
bounds, execution-error allowances or a receiver/IMU error law.
