# Bound the best linear contrast under the saved calibration boxes

The [calibration-resistant contrast](ESA_CALIBRATION_ORTHOGONAL_RESULT.md)
can tolerate only 0.48 micrometres of uniform position error per
coordinate. Determine whether any linear contrast under the same
calibration boxes and smooth-drift assumptions can tolerate much more.

Use the same two zero-field nominal conditional forecasts, physical
position units, 400 earlier epochs, 120 later epochs, and all 51
calibration terms per model. Keep the nominal contrast at zero on
the earlier coordinates, as in the prior conditioned comparison.
Use the same nine later constant, linear and quadratic terms. Allow
the proposed linear contrast to act anywhere in the same saved
earlier and later position representation, with exact cancellation
of all nine smooth terms. This allows a broader set of directions
than the numerical projections in the previous study.

Minimize the maximum absolute component of the difference between
the two affine forecasts, allowing their archived calibration boxes
and arbitrary smooth offsets. A numerical linear program may propose
the calibration vectors, the smooth offsets and a separation
direction. Verify the proposed vectors in the original boxes. Compute
the maximum coordinate discrepancy in exact arithmetic with no
reliance on solver status. Half that discrepancy is an upper bound on
the possible uniform nonlinear error allowance for any contrast
whose absolute coefficients sum to one.

For the proposed direction, enforce all nine moment conditions exactly.
Use the same exact support calculation over both full boxes to obtain
a lower bound on achievable error allowance. Compare both ends of the
resulting interval with the earlier submicrometre result and with the
original integration-error budget. The calculation will distinguish a
poor choice of direction from a limitation of the full calibration boxes.
It leaves open the smaller region supported by the earlier-loss
constraints, the full nonlinear trajectory, and prediction coverage.

Use only saved paths. Freeze the nominal forecasts, calibration matrices,
physical units, box endpoints and software checks. Allow two single-thread
linear proposals, using dual simplex and an interior-point method, at
most 2,000 iterations and 30 seconds each. Verify each proposal in exact
arithmetic. Recheck the earlier full-span direction as a lower-bound
reference. Freeze eight calls, 4,006 steps and a 180-second cooperative
allowance. Allow one additional recovery attempt with a separate
180-second allowance through the verified task runner.
No additional aircraft fits, later GPS observations or reserved flights
are used.
