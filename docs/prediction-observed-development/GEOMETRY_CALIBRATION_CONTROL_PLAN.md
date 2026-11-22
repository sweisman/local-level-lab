# Controlled route and climb calibration check

Question: With the same sensor limits and generated noise, does changing
earlier aircraft motion strengthen the weak Z-axis gyro-bias and vertical
accelerometer-bias directions?

Use four separate generated rotating-globe recordings at 55° north, crossing
two route patterns (eastbound straight and a broad course turn) with two
height patterns (level and moderate climb). Keep the 120-second duration,
first two-thirds training split, IMU and receiver noise laws, calibration
bounds, starting rule and numerical limits identical across the four cases.
Use the same random seed in each case for a matched noise comparison. Fit only
the generating physical model; this is a calibration-geometry control, not a
three-model decision study. The synthetic course follows the declared body
yaw and uses analytic position, velocity and acceleration derivatives.

First run a 10-second one-case technical preflight with a finite eight-fit-
evaluation cap. Qualify its source, tests and reboot recovery, then freeze a
separate four-case full study with at most 200 fit evaluations per case,
two one-thread workers and a one-hour cooperative wall allowance. Charge
native work before execution, preserve nonconvergence, and save the exact
inputs and outputs. Do not inspect observed or reserved ESA flights.

For each completed fit, report convergence, physical path adequacy, normalized
calibration recovery, local singular values, and the conditional whitened
Jacobian-column norms of Z gyro bias and vertical accelerometer bias. The
predeclared comparison is turning versus straight within each height pattern,
then climb versus level within each route pattern. This is a development
effect-size comparison, not calibrated aircraft coverage or evidence for an
Earth model. A failed fit remains a failure, not an invitation to change the
fixed limits.
