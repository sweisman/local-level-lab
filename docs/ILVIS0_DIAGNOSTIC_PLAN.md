# Focused NASA analysis plan after the October 11 review

After the active covariance/prediction comparison finishes, numerical recovery of
the 41 unfinished comparisons takes priority. Follow the four-step recovery sequence
in the [roadmap](ANALYSIS_ROADMAP.md): representative subset, a qualified solver and
larger finite budget, repeatability checks, then all 41. Additional diagnostics below
are deferred; retain their completed evidence and do not make their expansion a
prerequisite for attempting recovery.

Keep the 53-stretch first pass unchanged. It found 12 complete globe preferences,
no complete flat preference and 41 unfinished comparisons. Unfinished comparisons
provide no positive flat-Earth result. More completed fits still require separate
adequacy and uncertainty checks before calibrated scientific claims.

An **IMU (inertial measurement unit)** measures turning and acceleration. These NASA
records come from survey-grade airborne equipment. Exact device identification remains
parallel, lower-priority work; numerical and physical sensitivity tests can proceed
using the decoded measurements and stated assumptions.

## Evidence already available

The review identifies relevant weaknesses but does not cover several newer completed
tests. Those tests answer narrower questions than full scientific validation.

| Question | Existing evidence | Remaining question |
|---|---|---|
| Does reoptimization repair the header-clock error? | [Six clock fits](ilvis0-clock-trial-20261010/README.md) all converged. Control vertical error returned from 9.36 m at old parameters to about 0.70 m; globe/rotation preference survived. | Which interval do the increments physically represent, and how does calibration absorb the difference? |
| Is either Z correction individually essential? | [Calibration ablations](ilvis0-calibration-trial-20261011/README.md): zero gain completed all six fits and preserved preference; zero offset completed five of six. | What joint gain–offset combinations fit, and do their valleys depend on clock? |
| Is prediction tested? | [Retrospective split](ilvis0-prediction-trial-20261011/RESULTS.md): five of six fits completed. In the completed processing case, horizontal prediction error was 2.45 m for rotating globe, 142.9 m for still globe and 166.0 m for flat disc. | Does calibration transfer to predeclared other recordings, with appropriate uncertainty and dependence accounting? |
| Are numerical controls available? | [Software controls](ilvis0-solver-qualification-20261010/README.md) include short independently generated IMU/GPS data. The later scaling trial still completed only five of six observed fits. | Can a qualified solver recover realistic physical controls and stable optima for the archival problem? |
| Is temporal correlation documented? | [Epoch diagnostics](ilvis0-residual-diagnostic-20261010/README.md) preserve residuals and five autocorrelation lags. | What shared error model explains longer-lag, cross-axis and low-frequency behavior out of sample? |

The [verified-stopping trial](ilvis0-verified-stop-trial-20261011/RESULTS.md) completed
five of six fits and did not qualify. Its [saved failure audit](ilvis0-verified-stop-diagnosis-20261011/README.md)
identifies a bounded linear residual-step probe 1.55 times the stability limit despite
tiny cost change and gradient. The six-start allowance is spent; replication remains
deferred. This document grants no additional starts or corpus rerun.

## 1. Investigate clock and joint calibration

The [two-recording clock audit](ilvis0-clock-audit-20261011/README.md) is complete,
with no observed fits or native predictions. UTC tags accumulate 9.48 and 9.65 ms
more than nominal 200 Hz timing over the guarded stretches, about 22 ppm. The POS
elapsed-time tags also differ from nominal and from UTC. Neither establishes the
increment integration period by itself. Five independent physical controls passed,
including a gyro gain/offset/clock rank check. The actual timestamp grids can produce
about 20 m of synthetic stationary height error under an incorrect fixed-period
assumption; a tiny gravity adjustment removes most of that control's error. The actual
fitted gravity changes are larger and opposite in sign, so the full three-dimensional
compensation path remains unexplained. Preserve this distinction when planning profiles.

The [coupled three-dimensional controls](ilvis0-coupled-controls-20261011/README.md)
are now complete. Independently integrated force/angle increments recover known motion,
and the Python strapdown primitive agrees with a separate reconstruction. Interior and
near-boundary calibration references recover under QR and SVD linear solves. A coordinated
clock/calibration change preserves packet-endpoint positions but is distinguishable when
position observations have independent physical time tags. These controls use a Cartesian
frame with zero background/transport terms and known reference attitude. They do not yet
qualify the native geographic fitter, its receiver association or nonlinear optimization.
The separate [geographic controls](ilvis0-geographic-controls-20261011/README.md)
extend that check through the actual native value/tangent kernels and nonlinear solvers.
They use independent increments and off-packet receiver epochs for all three geographic
models, with six free calibration, initialization and latency parameters. All 24 fits
passed convergence/prediction checks, with track errors below 6 micrometres. The
[saved calibration audit](ilvis0-geographic-controls-20261011/CALIBRATION.md) nevertheless
finds a weak Z gyro-offset direction: interior offset errors reach 0.647°/hour, and
all 12 near-boundary fits reach the offset limit. The
[interval and geometry comparison](ilvis0-interval-controls-20261011/FINDINGS.md)
now separates these effects: all nine new fits passed; halving the interval reduces
offset error roughly fourfold, and added roll substantially improves recovery at the
same fine interval. This supports the proposed mechanism in the controls, without
identifying the NASA boundary cause. The completed
[original-rate coning/sculling controls](ilvis0-compensation-controls-20261011/FINDINGS.md)
now recover the known offset within 0.000011°/hour for both globe truths and
0.000377°/hour for the disc truth, with both corrections enabled. All nine new fits
passed, without changing the original solver or limits. Calibration conditioning
remains weak. The [latitude/convention controls](ilvis0-latitude-controls-20261011/FINDINGS.md)
now pass all 24 fits at ±45°, including opposed starts and roll/unequal timing.
Offset errors stay below 0.00079°/hour and no fit reaches a calibration limit.
Already-compensated controls demonstrate the error from applying corrections twice.
The [six-fit observed integration comparison](ilvis0-integration-trial-20261011/README.md)
is complete: four fits converged, while both zero-field globe fits exhausted their
budgets. The [saved-result audit](ilvis0-integration-audit-20261011/README.md) finds
their stationarity errors remain 53–56 times the limit. Z gain and offset remain
at exactly the original limits in all six fits. The alternative does not qualify
for archive rollout. The [full-column derivative check](ilvis0-latitude-controls-20261011/DERIVATIVES.md)
passed; it does not qualify global optimization. Do not assume the archive lacks
upstream compensation. Good predictions do not qualify unique
calibration. These short-record tests do not qualify all 27 archival nuisance parameters
or authorize observed profiles.

Start with a timestamp audit on the already selected recordings. Preserve packet order,
configuration, integer increments and original timestamps. Record both time tags and
their declared types, quantization, nominal cadence, adjacent differences, discontinuities
and cumulative departure from the declared sample period. Split incompatible configurations
and time discontinuities; never repair science measurements by interpolation.

A packet timestamp is not automatically its integration duration. Generate small,
independent controls with known increment periods and separately varied timestamp jitter
or clock scale. Establish what either integration convention recovers. Where Group1
engineering channels help check timing, label them fused navigation and use them only
for decoder validation. Investigate the vertical effect through accumulated velocity,
gravity correction and timing/calibration sensitivity. A smaller rotating-globe cost
alone cannot identify the clock convention.

The [first joint grid](ilvis0-z-profile-audit-20261011/README.md) is complete:
27/27 fits converged, using 4,174 native sweeps. Under original integration,
packet-header timing and no upstream field removal, all nine Z gain/offset pairs
favor globe, then the specified field. The preferred model's cost varies only 2.58%;
horizontal error stays 0.081–0.093 m. Its remaining boundary count is 0–1, versus
12–13 for zero-field globe and 13 for disc. The weakest remaining direction is
dominated by gravity correction and X/Y gyro gains. This demonstrates robustness
across tested Z corrections, not unique calibration.

Two approved, separately frozen follow-ups use the same grid:
[profiled upstream removal](ilvis0-z-profile-removal-20261011/PLAN.md), then the
[earliest predeclared other recording](ilvis0-z-profile-replication-20261011/PLAN.md).
Both have finished: removal converged 27/27, while the other recording converged
25/27. Seven complete nodes favor globe; two remain unresolved. Their allowances
are spent and no retries are authorized. A saved-only audit now examines their
calibration behavior and stopping failures. The second is a whole-stretch robustness check, not the deferred
training/prediction replication. Further clocks, the second predeclared recording
and archive rollout remain outside this allowance.

The [completed saved-only audit](ilvis0-z-followup-audit-20261012/README.md) preserves
all 81 grid fits and their original statuses. Both unfinished fits pass saved stationarity
but lack solver-reported success at their budget ceiling. Preferred control fits keep
near-zero removal and almost unchanged costs. Epoch files reproduce all saved costs
and RMS values. The [completed covariance audit](ilvis0-residual-covariance-20261012/README.md)
adds longer-lag, cross-axis and spectral diagnostics; these saved checks do not
calibrate uncertainty or authorize retries.
At each fixed gain/offset pair,
reoptimize all remaining parameters with their existing physical bounds. Use identical
grid coordinates, initialization policy and finite allowances for specified-field globe,
zero-field globe and stationary disc. Later stages compare clocks and processing assumptions.
Reuse only compatible completed reference points with verified provenance. Save the
absolute cost and within-model cost increase, stationarity, completion, remaining
boundary values and prediction errors.

Show each model's feasible region, fitted points and profile contours. Mark unfinished
points explicitly: their achieved costs are upper bounds on the unknown minimum, not
completed contours. A coarse grid cannot demonstrate a narrow minimum. Describe movement
of valleys across clocks and whether preference persists along admissible calibration
alternatives. Do not convert cost contours into confidence regions before uncertainty
calibration, or interpret cross-model relative contours as absolute model ranking.

**Cost must be explicit before launch.** Even a 3 × 3 grid across three models,
two clocks and two processing cases creates 108 fit identities before any permitted
reference reuse. It is not a cheap six-fit follow-up. Choose a staged grid and solver
only after reviewing the failed qualification and testing the numerical method, publish the exact identity ledger and
request a finite allowance. No adaptive restarts or expansion are implicit.

Success is an explained timing/calibration interaction and a stable complete comparison
under defensible alternatives. Persistent ambiguity remains a reported result; it is
not permission to add flexible drift until the fit looks better.

## 2. Establish a shared residual-error model

The [completed saved-only audit](ilvis0-residual-covariance-20261012/README.md)
reports dense lag curves, cross-axis covariance and correlation, and low-frequency
power in physical errors and declared innovations across all 81 grid fits. It retains
sample counts, actual lag durations, cadence and the limited frequency resolution of
these two short recordings. Irregular timestamps receive no FFT; measurements are
never resampled. Physical track errors use a common reference metric across models.
The control's vertical innovations retain substantial minute-scale dependence,
with less slow dependence on the other date. Neither the objective nor rankings change.

Relate those diagnostics to available receiver quality and precision fields. If a field
is absent, report it absent. Fix quality is not a measured noise variance. Fitted residuals
combine receiver error, inertial error, parameter estimation and model mismatch; they
do not uniquely estimate GPS covariance. Very small whitened RMS does not by itself
establish exceptional sensor accuracy or a calibrated likelihood.

The [shared error-model plan](ilvis0-residual-covariance-20261012/ERROR_MODEL_PLAN.md)
is prepared. Its [35 independent software checks](ilvis0-error-model-controls-20261012/README.md)
now pass: positive-definite covariance, cross-axis transformations, whitening and
train/prediction conditioning, including irregular times and fixed drift anchors.
These known-mean/known-covariance controls do not include fitted-parameter uncertainty;
The [training/prediction extension](ilvis0-error-training-controls-20261012/README.md)
now passes 26 controls for training-only covariance selection, linear-mean uncertainty
and sensitivity to all supplied covariances. Nonlinear calibration, active bounds
and integrated covariance-parameter uncertainty remain outside these controls;
specify their treatment before any observed comparison.
The [nonlinear geometry checks](ilvis0-nonlinear-uncertainty-controls-20261012/README.md)
now retain active columns, report nonlinear remainders and deficient rank, and keep
disconnected sampled support. Their boundary-distribution control demonstrates why
interior Gaussian covariance and likelihood thresholds cannot be transferred unchanged
to bounded estimators. Finite prediction ranges are sensitivity checks, not calibrated
intervals. The [native adapter controls](ilvis0-native-uncertainty-controls-20261012/README.md)
now verify all 27 derivative columns on six independently constructed geographic paths.
Training rank uses training predictions only. The [finite comparison preparation](ilvis0-prediction-covariance-preparation-20261012/README.md)
specifies 12 matched starts and at most 3,060 native sweeps, including all nonlinear
diagnostics. The [durable runner](ilvis0-prediction-covariance-20261012/README.md)
now passes 39 targeted controls and has its own launch freeze. A separate finite
observed-data allowance was approved and the comparison is running. Preserve the original comparison.
A separately versioned correlated-error objective remains a development alternative.
Estimate its parameters on designated development or training observations and
apply the same sealed covariance specification to all physical models. Compare direct
prediction errors as well as covariance-adjusted costs. Account for cross-boundary
correlation, fitted-parameter uncertainty and active bounds in future predictive intervals.
Retain the original objective and its findings unchanged. An absolute-fit threshold
requires independent calibration covering the shape hierarchy and selection procedure.

## 3. Identify the measurement contribution

Group 10001 is the primary-receiver stream, separately recorded from Group 1 fused
navigation. Cite the [interface specification and source checks](ILVIS0.md#measurement-provenance-and-independence)
in the eventual paper. A versioned provenance supplement should retain receiver-type
codes, original NMEA identifiers, stream hashes and historical firmware/layout evidence.
Do not alter the active freeze. Separate streams do not establish independence from
GPS coordinate conventions or statistical independence of measurement errors.

Specify matched controls for gyro increments, acceleration increments, gravity and
receiver-coordinate metric. State exactly which inputs each alternative uses in its
objective, initialization and motion constraints. Removing a channel from the objective
while retaining it elsewhere does not isolate its contribution.

A receiver-constrained angular-increment diagnostic should compare observed Group4 gyros
with each model's explicit trajectory-based prediction. Declare all attitude, mounting,
timing and gravity assumptions. Do not replace absent gyro observations with Group1
angular rates or differentiated fused attitude. Unknown body attitude or yaw can leave
such a diagnostic unidentifiable; report that rather than fabricate an independent test.

Include non-gyro controls with comparable nuisance freedom to ask whether coordinate
conventions and acceleration alone reproduce the separation. A flexible receiver-only
interpolator is not a fair model-comparison control. Report physical track errors in a
common metric, objective errors in their declared covariance, and rank after each ablation.
Horizontal-only, altitude-only and height/geoid variants remain useful, with covariance
transformed consistently. Receiver coordinates still originate in a geodetic navigation
system; these controls isolate dependence rather than create raw GNSS range evidence.

Success is a reproducible explanation of which measured combinations supply separation.
Interacting channels need not admit a single percentage of evidence attributed to gyros.

## 4. Qualify optima, prediction and independent replication

Extend existing controls to longer independently generated physical records, every model,
both clocks, coupled calibration errors, exact/near-boundary optima and poor starting
conditions. Compare at least two numerical strategies within the same feasible region.
Require objective recovery, predicted-observation agreement, repeatability and honest
treatment of unidentifiable combinations. Recovery of individual parameters is required
only where the control identifies them. A higher completion count alone is insufficient;
a converged poor flat fit and an unfinished flat fit are different outcomes.

Any larger-budget sensitivity gets a new freeze and allowance; the original 200-evaluation
records remain unchanged. Software controls do not establish full archival qualification.

Maintain a ledger of source hashes, aliases, UTC overlap, flight/date, platform and
supported physical instrument/installation continuity. Configuration bytes alone do not
identify a physical IMU. Overlapping streams and same-flight intervals are dependent
observations. Unknown identities remain explicit and conservatively grouped.

Use the already predeclared other recordings for the next prediction replication after
qualification and separate approval. Fit nuisance parameters on training observations
only, propagate original increments without receiver resets, and report all failures.
The completed control split is retrospective because its full recording was examined
earlier. Different recording files are not automatically independent installations.
Shared calibration across flights requires supported continuity and equal treatment of
all candidate models.

## 5. Rotation-field work follows these checks

Before estimating the free field, examine the actual latitude/heading coverage and rank
of north amplitude, east component and vertical amplitude against supported installation
biases and upstream-removal assumptions. If the field and removal are indistinguishable,
report their retained combination. More time samples or more files do not automatically
remove that ambiguity. The [rotation-field plan](ROTATION_FIELD.md) retains the later
solar-versus-sidereal magnitude test; gain, clock scale and common systematic errors need
precision appropriate to that much smaller separation.

The public milestone is a finished matched comparison with explained calibration,
credible predictive adequacy and robustness, followed by supported independent replication.
The survey-grade archive remains the primary project. Consumer stationary measurements
remain a separate developing experiment and inherit none of its thresholds.
