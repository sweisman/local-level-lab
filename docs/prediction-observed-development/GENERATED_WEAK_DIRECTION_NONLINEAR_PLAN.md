# Finite nonlinear check of the shared weak direction

The saved SVD audit found nearly the same weak local calibration direction
in both generated 900-second fits. Test whether moving along that direction
changes the future physical path more than the training path, and whether the
saved tangent predicts the change.

Use the sealed increment and point cases only. Reconstruct their exact
generated IMU and earlier receiver inputs from the frozen recipes and verify
all saved input hashes before native work. Keep the original fitted point,
model, processing case, clock, 600/300 split, calibration box and truth.
Select the box-feasible sign from the parameter values alone, preferring the
negative sign when both work. Evaluate the original point plus displacements
of 0.05, 0.10 and 0.20 normalized units along that sign. Do not fit, tune the
steps or select a direction using future errors. The baseline native forecast
must reproduce the sealed forecast before perturbations are accepted.

For each law, reserve exactly four full native forecasts, each with 270,000
IMU packets and 900 queries. Charge calls and packet visits before execution;
bound construction, builds and two one-thread workers separately. Freeze
source, environment, recipe, artifact hashes, finite limits and recovery
tests before launch. Preserve every failure and do not retry completed tasks.
At most two total numerical threads are needed. A short source-bound native
preflight and reboot-recovery qualification must pass first.

Report training and later physical path change from the fitted baseline,
plus the nonlinear-minus-tangent remainder, in north/east/up metres. This is
a development diagnosis on two previously opened synthetic paths. It cannot
establish coverage frequency, real-aircraft error or a model decision.
