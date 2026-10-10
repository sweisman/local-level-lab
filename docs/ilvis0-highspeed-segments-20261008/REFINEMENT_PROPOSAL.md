# Bounded numerical refinement proposal

The purpose is to make more of the existing shape comparisons finish, while preserving
the physical question, the same measurements and the same nuisance bounds. This is a
new development experiment. The completed 53-stretch study remains frozen.

The [saved-result diagnosis](POST_RUN_REVIEW.md) identifies 119 evaluation-limited fits,
including 42 that passed the saved stationarity test. Small singular-value ratios and
frequent parameter limits suggest that weakly constrained parameter combinations are
making numerical stopping difficult. This is a hypothesis to test, not a demonstrated
solver defect or evidence that accepting unfinished fits would be safe.

## Scope and comparison

Use two complete, previously selected stretches. Select them by numerical completion
and observable matching, before using model cost differences:

| Role | Source | Stretch identity | Duration | Median receiver speed |
|---|---|---|---:|---:|
| Unresolved diagnostic | `ILVIS0_applanix_57320_610_LVIS_38614965.013` | `b4e44ddc0f130ecd45674c78` | 7.22 min | 824.94 km/h |
| Completed control | `ILVIS0_applanix_57300_610_LVIS_38614965.013` | `570b37d23af5e245dd461051` | 7.30 min | 878.06 km/h |

Choose the unresolved stretch from the seven with all six saved stationarity checks
passing, maximizing the number of completed fits and then sorting by identity. It has
five completed fits. Choose the control from the fully completed stretches of the same
IMU type, prefer the same recorded installation signature, and minimize the sum of
relative duration and speed differences; break ties by identity. Both use IMU21 and
have the same recorded installation signature. That does not prove that the physical
installation was untouched between recording days; the files are not joined.

Reuse their exact intervals from the hashed selection. For each, fit rotating globe,
still globe and stationary disc under both existing processing cases. Use the original
zero initialization, complete raw-increment integration, receiver observations,
clock hypothesis, covariance, bounds and whole-stretch residuals. Preserve the original
initialization: force-derived accelerometer gains, zero other normalized coordinates,
and zero Earth-rate removal. The earlier shorthand “zero initialization” did not
describe the accelerometer-gain initialization in the frozen worker. Saved minima are the
baseline; do not spend starts rerunning the old solver. Do not use fused navigation as
an independent observation.

## Method to prepare before launch

1. Test a separate solver prototype on cheap analytic least-squares problems with known
   optima: an interior optimum, an optimum on a bound, redundant parameters, poor
   conditioning and an exhausted evaluation allowance. Require stationarity and
   demonstrated step/cost stability at the returned point; merely passing a small
   gradient at the budget limit must remain unresolved.
2. Preserve the physical feasible set and all nuisance directions. Evaluate explicit
   scaled projected-gradient stopping with stability checks, addressing the difference
   between the solver's raw stopping condition and the existing independent scaled
   stationarity check. Do not simply relax the old gate or relabel its 42 results.
3. Before the first observed fit, fix the exact algorithm and tolerances, test them, and
   hash sources, inputs, selection, configuration and numerical environment into a new
   manifest. Persist immutable identities, starts, failures and interrupted charges.
4. Save projected-gradient components, bound signs, singular values and right singular
   vectors at the final point. This identifies which parameter combinations are weak
   without inventing a new model-test rank cutoff.

Prototype checks must pass before any airborne starts. A failed prototype or trial is
reported as such; it does not justify more starts or looser thresholds.

## Finite compute allowance to approve

Approved maximum: **12 observed starts, one per identity, 200 native evaluations per
start**, including initialization and final diagnostics. No retry reserve, automatic
budget increase or expansion to the other stretches. Every interrupted start counts.
Use at most two total numerical threads. This is approximately **1.3 hours at the
completed study's median fit time, or 2.4 hours at its maximum**; these are estimates,
not guarantees. This allowance applies only to the separately frozen two-stretch trial
described in [its guide](../ilvis0-solver-trial-20261010/README.md).

Report both successes and failures. Compare numerical completion, final stationarity,
objective values, residual consistency and parameter limits against the saved baseline.
If the completed control changes its model preference or worsens materially,
investigate before extending. Report all changed costs; do not choose the method based
on whether it increases globe support. An improved local optimum does not establish a
global minimum, calibrated significance, accurate uncertainty or resolved onboard
processing.

Interpret shape first, and expose rotation only after the required converged comparisons
consistently favor the globe. Keep scientific decisions at abstain. Any later expansion
or physical assumption change requires its own finite scope and separate freeze.
