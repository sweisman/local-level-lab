# Clock cover and residual jumps

For a fixed affine path, the ideal query is q(s)=t+c+s d, with 0≤s≤1.
The packet endpoints are the native sequential binary64 sums. For nonzero d,
each interior crossing is s=(end−t−c)/d. Sorting those exact rational crossings
provides a complete partition for this ideal affine query. Open segment
interiors and exact node ownership are recorded separately. The native ≤ test
assigns an exact tie to the earlier packet, even when only an isolated endpoint
of the path belongs to that packet.

The partial fraction is (q−start)/dt. Because the rounded cumulative end need
not equal start+dt in real arithmetic, a branch can require a fraction just
above one. The report preserves that overshoot, the cumulative discrepancy and
whether the native fraction guard supports it. This does not prove coverage
of rounding in the native query multiplication, addition or predicate.

For a piecewise smooth residual r, let h=r′ on each open segment. Then

\[
r(1)=r(0)+\int_0^1 h(s)\,ds+\sum_c [r]_c
        +[r]_{0+}+[r]_{1-}.
\]

Here the endpoint terms mean r(0+)−r(0) and r(1)−r(1−). The integral uses
the previously checked piecewise trapezoid allowance, with the interior
one-sided derivative values at 0 and 1. All signed residual-jump intervals
are added outward. Bounds on jumps in h and h′ remain required independently;
they are not substitutes for jumps in r. Missing bounds, including endpoint
zeros, fail.

The jump component verifies this arithmetic under supplied piecewise smoothness,
partition and jump assumptions. It does not establish those assumptions for
native trajectories or qualify any observational confidence level.
