# Next component: rotation/gain support of the force matrix

The completed vector-norm comparison passes correctness but misses the existing
usefulness gate. Preserve it without retries or more facets. Before recomputing
native bounds, test a stronger necessary property of the existing force matrix.

For column j, M_j = R_initial R(p) e_j / (1 + g_j), where R(p) is a rotation.
For any fixed direction q, Cauchy–Schwarz gives
qᵀ M_j <= ||R_initialᵀ q|| / (1 + g_j).
This remains valid without assuming the supplied initial matrix is exactly
orthogonal. Gain domains must stay strictly above -1.

The reciprocal is convex. Its exact chord over the original gain interval is
an upper bound; when that interval is a point, use the exact reciprocal.
Substitute the existing affine matrix and its nine normalized remainder
coordinates. Export each necessary inequality with an explicit outward
coefficient-rounding correction over the original complete box. Retain the
existing zero-error center convention with a reported nonnegative relaxation.
Use 26 fixed integer directions transformed by the expansion-center rotation,
for each of three columns. Directions must depend only on the shared source and
declared expansion, never future truth or fitted outcomes.

Local tests must independently check reciprocal chords, axis ordering, signs,
point/gain-boundary domains, source rejection, exact export, physical retention
and exclusion of a norm-admissible but impossible outward matrix stretch.

After those tests pass, freeze 24 generated identities: the six configurations
crossed with full, sector, point and gain-boundary domains. Allow 64 independent
Rodrigues/force probes each: 1,536 probes and 119,808 exact inequality checks.
Four workers use one thread each, at most 180 cooperative seconds. No native
calls, original aircraft reads, observed starts, retries or protected outcomes.

Only after qualification passes, freeze a saved-only comparison of all 48
original cases. Preserve all 51 columns, prior constraints, physical/error bounds
and valid certificates. Allow 288 LP proposals, 1,152 exact support evaluations
and 300 cooperative seconds, with four workers/one thread. Save predictions
before reading future truth; independently reconcile every support certificate.
The twofold usefulness target stays unchanged. Neither success here nor an
unmet target qualifies aircraft error coverage or whole-program floating-point
enclosure. Further duration expansion and observed predictions remain gated.
