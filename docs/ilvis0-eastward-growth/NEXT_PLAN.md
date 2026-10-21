# A direct remainder bound for the rotating force source

The trace identifies the source and its accumulated residual velocity as the
next targets. Preserve the completed traces, including both time-limit failures.
Do not shrink calibration, timing or observation-error assumptions.

## Mathematical construction

The source has two pieces: `A = R f` and `B = R (P - I) f`. Here `R` is the
mount rotation, `P` the product of corrected gyro rotations up to the query,
and `f` the initial corrected specific force. All depend on the same calibration.

For each gyro rotation argument, independently bound its change `d_i` and its
first-order remainder `r_i` around the declared reference. Orthogonal rotation
products give a conservative prefix change at most `min(2, sum(d_i))` and a
prefix remainder at most `sum(r_i) + sum(d_i)**2 / 2`. This follows from the
first- and second-derivative operator bounds for products of skew exponentials;
it must be checked on independent noncommuting-rotation controls.

For `B`, let `s` bound the norm of the fixed initial mounting matrix, `d0`
bound the nominal `P - I`, and `f0` bound the nominal force. Let `dR`, `dP`,
`df` be change bounds, and `rR`, `rP`, `rf` be first-order remainders.
A conservative remainder about the ideal reference derivative is:

```text
rR*d0*f0 + s*rP*f0 + s*d0*rf
  + dR*dP*f0 + dR*d0*df + s*dP*df + dR*dP*df
```

For `A`, the corresponding bound is `rR*f0 + s*rf + dR*df`.
These are norm bounds, not an assumption of independent calibration errors.
Include the measured numerical mounting-matrix defect; do not assume exact
orthogonality merely because a matrix is nearly a rotation.

## Required implementation checks

1. Establish exact rational change/remainder bounds for the bias/gain
   calibration map with strictly positive denominators. Include the query's
   clipped packet fractions, both boundary sides and the preserved reference
   derivative convention. Do not treat increments as instantaneous rates.
2. Qualify the rotation-product and product-remainder inequalities independently,
   including zero motion, noncommuting axes, nonzero references, changing gains,
   clock-boundary crossings and deliberately conservative domains.
3. Reconcile the ideal reference value and derivative with the actual supplied
   numerical center and all 27 rows. A certified point-derivative enclosure is
   needed; a floating Jacobian agreement tolerance is not an error bound.
4. Intersect the new certified radius with existing valid radii only after
   source, reference and domain checks. Then require all native controls and a
   finite full-history usefulness screen before a complete comparison.

Each numerical study needs a new finite freeze. Component tests do not qualify
recording-scale uncertainty or whole-program floating execution. Keep all six
model/processing groups in eventual qualification and use training observations
alone to constrain calibration. No aircraft or protected ESA work follows from
this plan alone.

[Trace interpretation](INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
