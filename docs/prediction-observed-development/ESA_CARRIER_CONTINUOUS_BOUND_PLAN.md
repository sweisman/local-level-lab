# Bound all smooth trajectory errors at the saved ESA score times

Use the same four satellite sets, example limits and fixed satellite
geometry as the [earlier path search](ESA_CARRIER_MOTION_WITNESS_RESULT.md).
Use every distinct carrier epoch and score time as a knot. The position
anchors are among those knots. The natural cubic interpolant of any
trajectory with square-integrable acceleration gives the same
positions and uses no more acceleration energy. To see this, subtract
the interpolant from the trajectory and integrate the cross term by
parts. The difference is zero at the knots and the interpolant's second
derivative is continuous and zero at the two endpoints. The cross term
vanishes.

For each set, use the checked bounded solver with at most 60 iterations.
Compute a lower bound from a feasible path and an upper bound from a
separate check of the score weights. Reduce both range-error caps by
the known geometric remainder for the feasible path. To get an upper
bound for the actual fixed-transmit geometry, multiply the tightened
upper bound by the larger ratio of relaxed to tightened range caps.
Scaling down any relaxed path by that ratio puts it inside the
tightened limits without increasing any other error.

A directly checked path reaching the original score gap establishes
a possibility under the example limits. An upper bound below the
gap excludes such a path within the error model. If the bounds
straddle the gap, there is no decision. The result supplies no
independent bounds on the actual aircraft's errors.

Use one task, one numerical thread, 245 charged checks and at most
180 seconds. Only use sealed ESA 187 material. Run zero new physical
model fits, original downloads or reserved-flight reads.
