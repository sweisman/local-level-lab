# Saved correction audit for the final unresolved stretch

The completed full free-timing trial passed both controls but failed all four
target stability checks. Primary and repeat predictions agree closely in both
processing cases. All target fits reject proposed decreases, even after the
trust region becomes small. This audit separates affine-solver behavior,
timing geometry and nonlinear disagreement before another observed test.

Use only the sealed four target residual/Jacobian artifacts, saved fit histories,
receiver timestamps and packet count from the completed trial. Never decode an
original recording, run native integration or start an observed optimization.
Preserve all failed labels, original models, physical bounds and stopping limits.

One batch permits **12 bounded affine solves** (original full-space BVLS,
range-scaled full-space BVLS and fixed-timing BVLS for each target), **eight
singular decompositions**, and **4,120 saved-clock queries**, on four total
numerical threads. Each solve retains the existing 100-iteration ceiling and
10⁻¹⁰ tolerance. No retries or reuse of a completed allowance. Hash source
artifacts, software, environment and this plan before execution; verify them
again before sealing completion. Rendering completed evidence performs no solves.

Report signed affine cost change against the feasible zero step, correction
coordinates, projected physical prediction change, agreement with the saved
full correction, singular spectra, nearby representable clock transition and
the number of receiver epochs whose packet assignment changes along each step.
Report accepted/rejected optimization steps and their predicted/actual decreases.
The fixed-time result is a diagnostic restriction, never a full convergence gate.
Affine predictions cannot establish fresh nonlinear stability or resolve a flight.

After this audit, any observed derivative, boundary or corrected-point checks
require a new finite freeze. Numerical convergence is necessary but does not
establish absolute model adequacy, statistical significance or field causation.
