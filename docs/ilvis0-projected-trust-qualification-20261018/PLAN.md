# Trust-region qualification for receiver-coordinate refitting

## Preserved baseline and candidate

The earlier projected-fitting qualification failed and remains immutable.
Its fixed-endpoint diagnostic found large corrections whose linear prediction
fails in the actual nonlinear calculation. Rescaling did not help.

Reuse `ilvis0_solver_trust_v2` through a separate projected adapter. It accepts
steps using actual versus predicted improvement, restricts rejected steps to a
trust region, and retains the undamped fresh stationarity/cost/position gate.
A constructed narrow-valley control also requires one bounded correction at a
rejected full trial point. Accept this combined move only when its actual cost
decreases sufficiently relative to the first linear prediction. Record it as a
two-step correction, not agreement with the linear model of the combined step.
The original engine source remains unchanged; its private extension fails closed
if the expected source layout changes.
Physical bounds and all active columns remain unchanged. Position stability
checks apply to retained receiver coordinates, with omitted axes explicitly
unchecked. Preserve complete traces and endpoint residual/Jacobian artifacts.

## Execution order

1. Pass constructed controls for curved valleys, exponential motion, exact
   bound optima, null columns, finite allowances and failure reporting.
2. Freeze the candidate, tests, numerical environment, prior qualification and
   independent generating equations before the generated-motion batch.
3. Run **all 24 declared cases**, retaining failures without retry: three
   models × two clock constructions × horizontal/height objectives × zero/opposed
   starting points. Do not stop merely because one case fails.
4. Compare paired starts on the same retained objective. Require every fit to
   pass fresh checks, retained-coordinate errors below 2 mm, cost no greater
   than the independent generating-parameter reference plus 0.01, paired cost
   difference at most 1e-8 × max(costs, 1), and paired retained-prediction changes
   at most 1 mm RMS / 1 cm maximum. Do not require unique nuisance estimates.
5. If this gate passes, continue with full-calibration/boundary controls before
   a small observed refit freeze. A failed gate blocks observed refits; diagnose
   saved traces without restarting the completed allowance.

The prior all-column derivative checks remain separate supporting evidence;
this candidate changes the step algorithm, not the native projection derivative.
Twelve-second generated trajectories test software behavior, not Earth-model
discrimination, real calibration or confidence coverage.

## Finite generated-motion allowance

- **24 optimizer starts**, each at most **160 tangent sweeps**, including all
  fresh acceptance checks; two additional diagnostic predictions per start.
- At most **3,888 native generated-motion calls total**, charged before calls.
- **Four total numerical threads**, one worker, **30 minutes maximum**.
- One batch, no retries or expansion; errors remain in the result inventory.
- **Zero original-recording reads and zero observed-data fits.**

Use an exclusive worker lock, immutable task identities, per-start journal
entries, atomic hashed outputs and preserved source snapshots. Never restart
a charged identity or completed batch. Publication reads saved artifacts only.
The complete archival comparison remains 53 globe / 0 flat / 0 unresolved.
