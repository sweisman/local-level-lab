# Checking the weak calibration directions

Early results from the fixed control run expose a numerical issue: some fits
already predict the known track to micrometre scale, yet their final stability
probe takes a large calibration step that worsens the fit. All nuisance columns
remain present. Constant-speed tracks cannot separately identify many of them.
These failures remain failures under the frozen rule.

After that run closes, inspect six fixed endpoints: the zero start under nominal
timing for each model and processing case. Using only their saved residuals and
Jacobians, compare the existing bounded correction with a minimum-norm
least-squares correction. Keep every column. Use the standard floating-point
rank rule, report the retained rank and singular values, and retain the original
parameter bounds. This check performs no integration or new fits.

The saved audit has six identities and at most two linear solves per identity,
charged before execution. It uses one worker with four numerical threads and
a 60-second cooperative wall ceiling. Inputs, source and environment are frozen
before launch. Its completion means the comparison was computed, not that a
replacement solver qualified.

If the saved calculation supports the diagnosis, test a separate solver
composition. It reuses the bounded trust solver and fresh position/stationarity
checks, but uses a minimum-norm undamped correction when it lies inside the
existing bounds. Otherwise it uses the existing bounded correction. The same
step rule must be used in the optimizer and final probe. Do not change tolerance,
calibration bounds, error weights, control histories or forecast checks.

Qualify the composition on the existing known-optimum nonlinear controls,
including boundaries and redundant parameters, before considering a new frozen
training/forecast comparison. Every new run needs a fresh identity and finite
allowance. No completed identity is retried; no failed label is overwritten.
