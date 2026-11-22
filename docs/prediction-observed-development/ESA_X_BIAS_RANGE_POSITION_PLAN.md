# Check the remaining X-bias range against the earlier position scores

Use the saved earlier weighted residuals and Jacobians for the three
profiled increment-law fits. Take the lower edge of the unresolved
positive X-bias range from the sealed direction profile. Keep the
earlier squared-loss allowance of 0.01 and all original calibration
bounds.

Compute a bounded linear least-squares proposal over the whole
positive range, with every other parameter allowed to vary. Use a
supporting plane and exact rational evaluation to bound the minimum
squared loss on that box. Convert the result to the minimum change
in the weighted residual that the nonlinear model would need to
recover the allowance. Separately use the existing affine support
calculation to bound the largest X bias anywhere in the original
earlier-loss box.

Bind the exact sources and inputs. Allow three bounded least-squares
proposals and three support calculations on one thread. Read only
saved earlier fit artifacts. No native propagation, new Earth-model
fit, later receiver position or reserved group. The results establish
what the linear models allow and leave the nonlinear error open.
Each calculation depends on its original trajectory model.

[Direction profile](ESA_X_BIAS_DIRECTION_PROFILE_RESULT.md) ·
[Exact endpoint replay](ESA_X_BIAS_POSITION_REPLAY_RESULT.md)
