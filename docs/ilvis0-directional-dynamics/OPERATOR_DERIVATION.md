# Componentwise reference-error bounds

For a common physical parameter vector, write each quantity as
`x = c_x + L_x + r_x`. The supplied bounds enclose both `|x − c_x|` and
`|r_x|` coordinate by coordinate. `L_x` is the declared reference linear map.
After reference rounding, a remainder may contain a constant error; it is not
automatically a pure second-order quantity. The caller must qualify the input
bounds and their reference coefficients.

## Algebra

For a scalar product, use the reference map `c_x L_y + c_y L_x`. Its residual is
bounded by `|c_x| R_y + |c_y| R_x + D_x D_y`, where `D` bounds total change and
`R` bounds reference error. Total change is bounded by
`|c_x| D_y + |c_y| D_x + D_x D_y`. Add the exact error between the exported
binary64 reference and the exact reference product to both bounds.

Matrix products and actions sum those terms over the relevant row and column.
Cross products retain their coordinate sparsity. Addition, fixed scaling and
transpose follow directly. No norm-based radius is assigned to an unrelated
coordinate. Exporting to a Euclidean interface uses an outward square root of
the sum of squared component radii. A declared matrix structure remains a source
assumption; checking the reference matrix does not prove it over an uncertain
domain.

## Scalar nonlinear operations

For `x = c + delta` on a domain excluding zero,

`1/x − 1/c + delta/c² = delta²/(c² x)`.

Thus a valid reference-error bound is
`R/c² + D²/(c² m)`, where `m` is a lower bound on `|x|`. The change bound is
`D/(|c| m)`. Include the exported reference's rounding error.

On a strictly positive domain,

`sqrt(x) − sqrt(c) − delta/(2 sqrt(c))`
`= −delta² / (2 sqrt(c) (sqrt(x)+sqrt(c))²)`.

Use checked lower square-root endpoints to bound the denominators, add
`R/(2 sqrt(c))`, and account for reference rounding. Upper square roots are
verified by exact squaring; their preceding binary64 values provide lower
endpoints. Unsupported domains are rejected rather than clipped.

## Norm-preserving rotation departure

Let `b` be a rotational departure of vector `a`, with
`|a+b|² = |a|²` throughout the supplied domain. Then

`2 a_z b_z + b_z² + E = 0`,

where `E = 2 a_h · b_h + |b_h|²`. If the vertical component retains its sign,
the stable branch is

`b_z = −E / (a_z + sign(a_z) sqrt(a_z² − E))`.

This avoids subtracting two nearly equal vertical magnitudes. The sign of both
`a_z` and `a_z+b_z` must be established over the whole domain, as must a
supported square-root and reciprocal domain. The norm identity must follow from
the actual source rotations, not from sampled agreement.

The value-only source preflight also accounts for the literal installation
matrix's metric defect. If `|a+b|²−|a|²` is bounded by `eta`, widen `E` by
`[−eta,+eta]` before evaluating the branch. For `a=R0 U f` and
`a+b=R0 U P f`, with proper `U` and `P`, a valid defect bound is
`2 |R0ᵀR0−I|_F |f|²`. The input matrix is not normalized. This bounds a value
interval; it does not supply native reference coefficients.

The formula also creates a reference linear map through its scalar operations.
Before its error radius can replace an existing native radius, those coefficients
must be shown to match the native reference map, or their discrepancy must be
propagated explicitly over the full parameter domain. Rounded reference vectors
and a norm identity alone do not establish that agreement.

These are isolated operator bounds. They are not a complete propagation method,
an observation-noise model or calibrated scientific evidence.

[Prototype status](README.md) · [Previous baseline diagnosis](../ilvis0-directional-prediction/BASELINE_DIAGNOSIS.md).
