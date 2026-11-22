# Bound the best earlier linear fit at the X-axis endpoint

Use the three saved earlier weighted residuals and Jacobians and
the three compensated points from the exact position replay. Fix
normalized X-axis accelerometer bias at +1. Let other parameters
vary over the entire original box in the saved linear model.

Take the tangent plane to the squared residual norm at each
compensated point. Convexity makes it a lower bound on the loss.
Minimize that plane over the box exactly with rational arithmetic.
From the resulting lower bound, compute the smallest norm of a
nonlinear residual correction that could restore the previous 0.01
earlier loss allowance at the endpoint.

Freeze the inputs and source first. Use one thread and three
certificates. Read no inertial samples or later coordinates. The
result applies to the saved affine model and does not bound the
nonlinear residual correction over the calibration box.

[Exact endpoint replay plan](ESA_X_BIAS_POSITION_REPLAY_PLAN.md)
