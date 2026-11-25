# Check bounded linear steps in the full derivative geometry

Use exactly the seven saved generated-flight derivatives, known targets
and 26-coordinate calibration boxes from the diagonal-scaling check.
Keep the added residual of 102 in rows the model cannot change. From the
same zero start, solve the bounded linear problem directly with the
existing dense bounded least-squares solver. Compare it with the same
solver after a reduced QR factorization of the original derivative.

QR discards the part of the residual perpendicular to every calibration
direction. That part adds a constant to squared error. The remaining
problem has the same minimum in the original coordinates, with the same
box and all columns, including weak directions. This tests the linear
correction and position check under a known optimum. It says nothing by
itself about the curvature of an observed fit.

For both methods retain the unchanged fresh-position, objective and
stationarity check. Require maximum error against the known linear
prediction of at most 0.0001 whitened units, as in the previous replay.
Record both methods and any failures, regardless of which passes.

Freeze seven tasks on one numerical thread. Allow nine charged operations
per task, including both bounded solves, the fresh checks and their
residual evaluations. The cooperative wall limit is 90 seconds. Use the
shared qualified task recovery. Decode no aircraft measurements and run
no native propagations, observed fits or reserved ESA reads.
[Previous scaling result](SCALED_SOLVER_REPLAY_RESULT.md)
