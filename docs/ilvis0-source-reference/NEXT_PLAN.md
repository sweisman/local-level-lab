# Carry the qualified source bound through the dynamic calculation

The six-source reference comparison is complete. Do not restart it or enlarge
its allowance. The saved affine radii improve every tested source group, so a
direction-aware dynamic candidate is justified; a complete prediction rerun is
still premature.

Preserve the existing training-conditioned force range and all shared error
columns. Use `A=R f`, `B=R(P−I)f` and the exact decomposition

`(Q R P−R)f = (Q−I)(A+B)+B`.

Here `Q` is the accumulated navigation-frame rotation. Retain separate component
bounds for `A` and `B`, especially the qualified vertical bound, through the
force action, velocity update and coordinate extraction. Keep the old global
norm bounds alongside component bounds where they are sharper; converting a
vector norm into three identical coordinate uncertainties can erase the gain.

The reference row used in any new operator must be explicit. Include center
rounding and any coefficient mismatch when replacing a bound. A source-only
match is not proof that every full-trajectory derivative is preserved. Do not
transfer the improved bound on the first force sample to later samples without
retaining their calibrated differences.

Qualify the candidate first against independent constructed motions and the
unchanged native control matrix, including all 27 physical and 24 shared columns,
both clocks, packet boundaries and all model/processing groups. Preserve
original centers and stationary-motion checks. Freeze a separate finite
qualification before execution. Compare actual baseline error allowances before
another full prediction trial; launch that trial only if the qualified candidate
improves the relevant allowances. Do not relax the existing width target.

No new observed-data fitting is authorized by this source result. The full
prediction and adequacy gates still precede retrospective aircraft predictions
and protected ESA confirmation work.
