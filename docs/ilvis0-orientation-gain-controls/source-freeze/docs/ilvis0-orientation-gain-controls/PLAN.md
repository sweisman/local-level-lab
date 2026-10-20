# Preserve the declared orientation range in matrix supports

The saved Gram diagnostic flags all 36 extreme matrices and retains all six
physical anchors. The next component must exclude impossible combinations
without discarding any permitted physical calibration. Do not repeat the
completed width or Gram diagnostics or infer narrower intervals from them alone.

## Necessary directional bound

For a fixed direction q and column j, put u = R_initialᵀ q and
y(p) = exp(skew(p_angle)) e_j. Let y0 be y at the declared expansion center.
Both y and y0 have unit length. Their distance is at most
D = min(2, ||p_angle-p_center||), bounded over the original physical box.

With a = uᵀ y0 and w = u-a y0,
uᵀ y <= a + |a| D²/2 + ||w|| D.
This follows from y0ᵀ(y-y0) = -||y-y0||²/2. Also retain the existing full-sphere
upper bound ||u||; use the smaller valid upper bound. This can give a negative
upper bound in the direction opposite a nearly fixed matrix column, preserving
the lower projection lost by the full-sphere constraint.

Evaluate the center rotation with the already qualified exact degree-40
polynomial and its operator-norm tail t. For polynomial column Pj, let
aP=uᵀPj and e=||u|| t. Then an outward support is
aP+e+(|aP|+e)D²/2+[||u-aP Pj||+t(||u||+|aP|)]D.
Use exact rational products and outward square roots. This is a mathematical
enclosure, not a whole-program floating-point certificate.

Divide the signed support H by 1+g_j. When H is nonnegative, multiply the
existing exact reciprocal upper chord. When H is negative, multiply the
reciprocal's lower tangent at the fixed center; its sign makes this an upper
bound on H/(1+g_j). A chord with negative H would be unsafe. Gain domains must
remain strictly above -1.

Use the same 26 fixed center-derived directions per column and all 51 columns.
Substitute the existing affine matrix and remainder coordinates, retain the
zero-error center convention with an explicit nonnegative relaxation, and
export coefficients outward over the original complete box. No future truth
or observed outcome may choose a direction or bound.

## Qualification and comparison

Local tests must check signed reciprocal bounds, point domains, polynomial-tail
allowances, source rejection, independent physical retention and exclusion of a
contracted column that the older full-sphere supports admit. Do not assume all
nonphysical matrices can be separated by these linear inequalities.

After local tests pass, freeze 24 identities: six generated configurations
crossed with full, sector, point and gain-boundary domains. Allow 64 independent
Rodrigues/force probes each: 1,536 probes and 119,808 new support checks.
Report any reused oracle validations separately. Four workers use one thread
each with a 180-second cooperative allowance; zero native calls or bounds.

Only after qualification passes, freeze all 48 saved sectors for comparison.
Preserve every prior constraint, physical/error bound and valid certificate.
Allow 288 LP proposals and 1,152 exact support evaluations, with four workers,
one thread each and a 300-second cooperative allowance. Save predictions before
checking known future truth; independently audit every endpoint. The existing
twofold target remains unchanged. No original aircraft reads, observed fits,
protected outcomes, retries or budget expansion are permitted.

Passing these components would not establish full physical realizability,
recording-scale usefulness or observational coverage. Longer and observed
predictions remain subject to their existing requirements.
