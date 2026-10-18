# Receiver-coordinate refitting controls

## Purpose and scope

Qualify the receiver-projection interface for nonlinear fitting using generated
motion whose receiver trajectory is known independently of the navigation
predictor. This is software development, not another synthetic Earth-model
campaign or a fit to archival observations. Preserve all completed studies.

Reuse the existing closed-form geographic controls: twelve seconds of level
eastward motion with changing body yaw and pitch, independently integrated body
increments, off-grid receiver epochs, and known calibration and timing errors.
The three physical models each generate their own truth. The nominal and
variable-interval constructions include interior and near-bound calibration.
Short controls verify the fitting interface, not Earth-model discrimination.

## Implementation

1. Add `lll.ilvis0_projected_fitting.ProjectedProblem`, wrapping the full native
   residual/Jacobian with `ReceiverProjection`. Preserve every active parameter,
   the full prediction interface, original initialization and covariance. Expose
   retained-coordinate physical errors separately from unscored coordinates.
2. Reuse the existing bounded-step solver with exact derivatives and fresh cost,
   stationarity and physical-position stability checks on retained coordinates.
   Explicitly label omitted coordinates as unchecked. Report numerical rank and
   abstain scientifically even when the numerical solution passes. This adapter
   is not a replacement for the qualified full-coordinate archival policy.
3. Test direct marginal-objective/derivative agreement for all 26/27 columns,
   independent-trajectory recovery, different starts, exact bounded optima,
   lost rank, invalid inputs and evaluation exhaustion. Do not demand unique
   parameter recovery when the retained observations cannot identify them.
4. Freeze sources, environment, finite limits and test identities before the
   final qualification batch. Publish the batch outcome and individual test
   records. Development test runs remain separate from this sealed batch.

## Finite qualification limits

- At most **24 generated-motion optimizer starts**: three models × two clocks
  × two coordinate subsets (horizontal/height) × two declared starts.
- At most **80 tangent sweeps per generated-motion fit**, including its fresh
  final check; at most two additional value predictions per fit.
- Six all-column native derivative controls, at most 56 sweeps each.
- At most **2,400 native generated-motion sweeps total**, charged before calls.
- Algebraic adapter/solver checks use constructed arrays, no native sweeps.
- One qualification test batch, **600 seconds**, **four numerical threads**,
  stopping at the first failed control, with no retries or allowance expansion.
  Compile local kernels once as needed. Unrun controls remain explicitly untested.
- **Zero original-recording reads and zero observed-data optimizer starts.**

Retain all columns after projection. Rank uses the declared floating-point SVD
cutoff; it is not an empirical identifiability threshold or a confidence interval.
For generated motion require independently known retained-position errors below
2 mm and objective recovery against the known-parameter reference; report
unscored-axis errors without using them to manufacture a pass or a failure.
Direct-marginal comparison must use the identical covariance and candidate.
Finite differences use the separate native value kernel; compare value agreement
in physical units at the established 0.3 micrometre tangent-control tolerance,
rather than requiring bit-identical accumulation between different kernels.

Development exposed a failed SciPy trust-region prototype on the near-bound flat
horizontal control: 80 sweeps did not meet stationarity, despite a 0.02 mm
retained-coordinate error. Its unscored height error was about 6.9 m. Preserve
that prototype and diagnostic separately; it has no qualification or observed
results. The sealed candidate reuses bounded steps and unchanged fresh-check
tolerances, rather than relabeling that failure or relaxing the acceptance gate.
Use the wider native arithmetic already used in archival recovery. It did not
eliminate the development height-only stopping failure; retain that result.
The explicit `qualify_ilvis0_projected_fitting.py` matrix is run by the study
worker, separately from routine CI tests of the adapter and failure reporting.

## Acceptance and next step

All frozen controls must pass. Any failure blocks advancement; preserve its
evidence rather than retrying the sealed batch. Passing qualifies this interface
and these controls only. A small observed refit proposal must separately freeze
its stopping/stability rule, model/case identities, starts, repeats and budget.
No archive rollout, changed 53/0/0 findings or calibrated significance follows.
