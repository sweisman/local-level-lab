# Correct the joint calibration using exact packet derivatives

Use the same 18 paired direction settings from the opened ESA flight.
For each shape, start at the saved earlier-selected joint proposal.
Use the exact packet rotation and its twelve calibration derivatives.
At each point remove the three starting-rotation directions from the
linearized update. Cap the initial box-constrained step at 0.25 per
normalized coordinate. Accept a step only if it
lowers the exact earlier mean squared chord loss. Reduce the step cap by
a factor of four after a rejected step. Retain rejected attempts.

Keep the same 10⁻¹⁰ maximum projected-gradient stopping limit and all
original calibration bounds. Allow at most six derivative evaluations
per shape, including the saved starting point. Report a failed stop as
unresolved. Keep the exact direction residuals as point diagnostics and
compare later angular errors only when both shapes meet the exact stop.
Neither the correction nor the stopping check uses the later directions.

Use 36 task identities, one numerical thread and a 180-second wall limit.
Each task can also perform one exact value-only replay after the earlier
fit ends. Store results task by task. Verify the method first on generated
noncommuting packet rotations with known interior and boundary optima.
No aircraft position fit, protected-flight access or new position forecast
is allowed. Local first-order convergence does not certify the global
calibration range or an observational error law.
