# Look for nonlinear compensation at the directional X-bias boundary

Use only the specified-field globe from the archived earlier position
study. Keep X bias at or above the positive bias boundary from the
sealed direction profile. Keep the other physical parameters in their
original boxes and use the original fixed earlier whitening factors.

Verify the saved baseline in the scalar integrator. Evaluate the
point changing only X bias to the lower boundary and the point
proposed by the saved affine range calculation. Starting from the
better of these two exact points, use its current exact residual
and the original Jacobian to propose a bounded correction. Keep
each normalized change within 0.05. Check the half and full steps
in the exact integrator. Repeat once from the best exact point.
Retain all seven integrator passes without selecting from later
receiver data.

Report the lowest achieved increase in earlier squared loss against
the original 0.01 allowance. Also report the actual nonlinear
remainder at every point. The two corrections search a small region.
They can supply a feasible example or retain a failure. They
do not bound the rest of the nonlinear region or refit the original
decision cases.

Freeze one task, one numerical thread, seven scalar calls and at most
two bounded linear proposals with 100 iterations each. No later
receiver positions or reserved flight groups. Test the acceptance
and step-bound logic on constructed residuals before launch.

[Earlier affine position bound](ESA_X_BIAS_RANGE_POSITION_RESULT.md)
