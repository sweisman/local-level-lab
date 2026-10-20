# Next component: keep calibration errors mutually consistent

The complete common-transform comparison passes correctness but misses its
fixed improvement target. Its saved-only audit passes. Further duration
expansion is deferred while the remaining conservatism is investigated.

The reference acceleration and the force-transform matrix depend on the same
physical orientation, accelerometer gain and bias. The current relaxation
allows their remainder coordinates to vary separately. Add only necessary
consistency constraints, with no tighter physical bounds, new drift process,
discarded orientation sector or extra fitted information.

## Mathematical candidate

Let the common matrix be M, reference specific force f, constant accelerometer
bias b and gravity g. Reference acceleration satisfies

    A = M (f - b) + g e_D.

Write M = M_c + J_M δp + E_M and A = A_c + J_A δp + E_A.
With b = b_c + J_b δp, the exact relation is

    E_A - E_M (f - b_c)
      = d_0 + (J_M (f - b_c) - M_c J_b + e_D J_g - J_A) δp
        - (M - M_c) J_b δp.

Here d_0 = M_c (f - b_c) + g_c e_D - A_c. Preserve centre and Jacobian
mismatches explicitly; do not assume different floating-point constructions
cancel exactly. Bound the final product over the entire original physical
region. Express the result as six outward necessary inequalities on the
existing 51 coordinates. Keep force/clock/reference bindings explicit.

## Qualification before use

First test the relation independently: exact affine controls, full rotations,
sector and point domains, gain boundaries, signs and every affected coordinate.
Use an independent rotation/force oracle and exact rational inequality checks.
Verify finite input validation, stale bindings, zero caps, outward coefficient
conversion and preservation of known physical calibrations. No sampled test
alone establishes the global bound.

Freeze finite identities, evaluations, environment and sources before the
component qualification. Only after it passes, prepare a separate saved-only
48-case comparison using the sealed training and future artifacts. It should
need no new native integration or observed fitting. Compare complete sector
unions, preserve every failure and keep correctness separate from narrowing.
Future truth remains unavailable until the revised prediction is saved.

If the candidate is invalid or unhelpful, publish that result rather than
relaxing the earlier target. Recording-scale usefulness, numerical enclosure
and observational-error adequacy remain prerequisites for new aircraft fits.
