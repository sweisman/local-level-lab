# Fitting with shared measurement uncertainty

Errors that affect several measurements together need a joint treatment. The new
research objective uses the complete covariance matrix, preserving correlations
between minutes, IMU axes and the GPS-dependent wind constraint. It holds that
matrix fixed as model and nuisance coefficients change.

The calculation first rescales rows to avoid mixing numerical magnitudes from
gyro rates and the wind constraint, then uses a Cholesky factor to whiten their
joint residual. Existing parameter penalties are applied afterward. A singular
or numerically unstable covariance produces an explicit failure; the calculation
does not discard measurement directions or silently add artificial noise.

It reports the residual quadratic and Gaussian normalization separately. The
normalization matters when covariance assumptions differ, even though it stays
constant during a fit with one frozen matrix. These outputs do not select a
correlation assumption, compare evidence across different wind models, or produce
a calibrated Earth-model decision.

All six saved recordings were checked under all 36 persistence assumptions,
giving 216 objective evaluations at their existing fitted parameters. No new
optimum was fitted. The same 79 supported minutes remain throughout, and every
scenario is preserved. Independent matrix solves and direct perturbations agree
with the objective and its derivatives.

The check exposed an important distinction: measurement uncertainty does not
describe all error in the wind approximation. The physical wind candidate already
allows a 2 m/s discrepancy in its speed constraint. Using propagated GPS errors
alone loses that allowance and gives excessive weight to the constraint.

A second frozen comparison therefore makes the existing allowance explicit:
full shared-input measurement covariance **plus** an independent model-discrepancy
component for the wind constraint. Shared GPS cross-correlations remain intact.
The broad wind candidate has no such constraint and is unchanged. No allowance
was tuned to the simulated truth or to achieve a model decision.

Across the three physical-wind cases, the measurement-only residual quadratic
ranges from about 27,700 to 598,000. Retaining the registered discrepancy changes
that range to about 167–336. Those are uncalibrated objective values at old fit
states, not goodness-of-fit probabilities or evidence for an Earth model. The
large change shows why a working likelihood must distinguish measurement error
from limitations of its nuisance model.

The implementation separates local sampling covariance from penalized curvature.
Neither is validated interval coverage. Covariances still come from provisional
error assumptions linearized at saved free-fit states; they are not an outcome-
independent design policy. Mounting, calibration, missing GPS correlations and
instrument/systematic uncertainty remain open.

All 44 focused tests pass. Both sets of 216 objectives are independently checked;
the broad-wind controls match their parent results. The first evaluation stage
took about 54 summed seconds, and the discrepancy comparison about 7 seconds,
using one numerical thread. Completed-scope resume checks skipped all cases.
No new flights, optimizer calls, bootstrap, calibration or production changes ran.

The next proposed comparison uses the six saved recordings under four fixed
GPS/IMU correlation pairs: independent/independent, 15s/15s, 300s/300s and 15s/300s.
Each would receive a free fit and three fixed Earth-model fits: **96 fits**, with
at most one predefined nesting repair per case/assumption, or 120 starts total.
This scope is proposed, not launched. It would retain the explicit discrepancy
component, freeze each covariance across model comparisons, and report convergence,
boundaries and raw objective differences without calibrated decisions. Runtime
needs measurement; no new flights or bootstrap are proposed.

The documented corpus contains the first stage's `plan.json`, six task-named
JSON/NPZ pairs, `review.json`, `verification.json`, `status.json` and `run.lock`.
The `wind-discrepancy/` subdirectory preserves the second stage in the same form.
Both bind sources, inputs, parent artifacts and numerical environment. Completed
artifacts and bound helpers are immutable. No worker remains active.
