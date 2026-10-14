# Next steps for the NASA airborne analysis

## Starting point

The preserved first study found 12 globe preferences. Completed recovery adds twenty-nine,
giving **41 globe preferences, zero flat preferences and 12 unfinished comparisons**
among the same 53 eligible stretches. All forty-one also favor the background-field globe
over the zero-field globe. Completed results now include both IMU8 and IMU21 recordings.
This is a substantial
empirical finding; unfinished calculations do not provide equal support for flat Earth.
A calibrated statistical significance level and independent-replication count still
require uncertainty validation and accounting for shared flights and instruments.
The [current findings](ilvis0-position-stability-trial-20261013/FINDINGS.md)
and [saved-result diagnosis](ilvis0-highspeed-segments-20261008/POST_RUN_REVIEW.md)
preserve what the measurements and calculations currently show.

“Rotating globe” and “still globe” below retain the exact names used in saved fits.
They compare the standard background angular-rate term with zero on the same globe
geometry. They are not verdicts on the field's physical cause or on heliocentric versus
geocentric cosmology. A stationary-Earth theory proposing a nonzero inertial field is
not represented by the zero-field candidate. Keep model preference, free measurement
of the field, and interpretation separate; see [the interpretation policy](ROTATION_FIELD.md#interpretation).

An **IMU (inertial measurement unit)** measures turning and acceleration. These are
survey-grade IMUs used for precision airborne mapping. Their published capabilities
provide a meaningful foundation for error assumptions. Exact device characterization
and producer documentation are **lower-priority parallel work**, not prerequisites for
continuing analysis. Use available system/family specifications, empirical decoder checks
and explicitly stated assumptions; investigate how those assumptions affect results.
Do not transfer one configuration's exact specifications to every recording or call an
assumed offset allowance measured drift. Unknown corrections matter where they prevent
a particular quantity from being separated, rather than stopping all modeling.

The covariance/prediction comparison has finished with 10 of 12 fits converged;
its combined comparison remains unresolved. The immediate priority is resolving
as many of the remaining 38 numerically incomplete stretches as possible.
The active wider run retains all 41 original recovery identities and reuses the
three completed subset stretches, preserving the earlier evidence.
Further diagnostic expansion is deferred. Numerical completion, fit adequacy and
statistical support remain separate checks; recovering a fit does not by itself
establish a calibrated scientific detection.

1. Freeze a small representative subset of the 41, covering numerical failure types
   and observable recording properties without choosing favorable model preferences.
2. Test a separately frozen numerical strategy and larger finite evaluation budget,
   retaining the physical models, calibration bounds and two processing cases.
3. Check objective agreement, valid stopping, repeatability and predicted tracks,
   including a completed control. Keep all original failures and results unchanged.
4. Apply the qualified method to all 41 in a separately budgeted recovery study.
   Preserve numerical failures and report newly complete comparisons explicitly.

The [recovery preparation](ilvis0-convergence-recovery-preparation-20261012/README.md)
records all 41 unfinished stretches and selects one from each of three numerical
failure categories, plus a completed control. This is metadata-only preparation;
the numerical strategy and finite evaluation allowance remain to be qualified.

The [continuation trial](ilvis0-convergence-recovery-trial-20261012/README.md) is
complete: 15/24 fits passed, including all six completed controls and eight of
15 unfinished primary fits. None of the three unresolved stretches became fully
resolved, so this method did not qualify for rollout. Its 24 starts cover 15 unfinished fits, six completed
control fits and three perturbed-start repeats. Each allows 600 fitting sweeps plus
two track checks; the 14,448-sweep ceiling estimates roughly 10–14 hours on two threads.
The finite allowance is recorded in the runtime freeze. Unchanged converged reference
fits are reused; original failures retain their labels.

The [saved stopping audit](ilvis0-recovery-diagnosis-20261012/README.md) separates
four early gradient failures, four early stability failures and one budget failure.
A known-answer, near-boundary software control reproduces one stopping failure;
the rectangular dogbox alternative passed 30/30 software controls versus TRF 29/30.
The [separate rectangular proposal](ilvis0-rectangular-recovery-trial-20261012/README.md)
preserves all physical assumptions, requires fresh stability verification, and
saves final Jacobians and evaluation traces. Its v2 trial is complete: 24 starts used
2,021 native sweeps; 8/24 fits passed, including all six completed controls but only
two unfinished primary fits and no perturbed repeats. No test stretch became fully
resolved, so qualification failed. Its saved traces and Jacobians support further
numerical diagnosis; software success did not translate into all-41 recovery readiness.

The [saved-tangent diagnosis](ilvis0-rectangular-diagnosis-20261012/README.md)
reproduces a boundary-start stall on an independent two-parameter control. Exact-bound
initialization improves completion on saved affine systems from 12/24 to 16/24;
the remaining weak directions involve gravity correction and gyro gains. The
[boundary-aware nonlinear controls](ilvis0-boundary-controls-20261012/README.md)
now pass 40/40 known-answer comparisons with bounded linear steps, versus 35/40
for the original method and 38/40 when only the start is snapped to the boundary.
All retain the same bounds and fresh stopping checks. The separate
[boundary-aware archival trial](ilvis0-boundary-recovery-trial-20261012/README.md)
is complete: 17/24 fits passed using 2,399 sweeps, including nine of fifteen
unfinished primaries, all six controls and two repeats. No test stretch became
fully resolved; the method did not qualify for rollout.
The [saved-result diagnosis](ilvis0-boundary-diagnosis-20261013/README.md) separates
six stationary stability stalls from one budget failure. All three predetermined
primary/repeat pairs agree in cost and track to within 0.13 mm on every axis, yet
have opposite stopping outcomes. Before another trial, isolate native prediction
and tangent accuracy near these endpoints, keeping the physical models and bounds
unchanged. Further budget alone does not address the six early stops.
No archival result is relabeled by these local calculations.

The separate [actual-position stability comparison](ilvis0-position-stability-trial-20261013/README.md)
checks the full model's predicted-position change instead of rejecting a correction
solely on its local residual prediction. It retains gradient and objective-change
limits, requires at most 1 mm axis-specific RMS movement and 1 cm at every epoch,
and preserves the old rule and results. These numerical tolerances are not claims
of receiver accuracy. Forty known-answer cases and independent short native motion
controls pass. The new finite trial uses all primary endpoints of the completed
boundary-aware study, the same four recordings, 24 starts and a 14,448-sweep ceiling.
No endpoint is chosen for a favorable cost or convergence result. Both primary and
perturbed starts must independently pass before an all-41 recovery freeze.
This trial is now complete and qualified: **24/24 fits passed**, including all
controls and repeats, using 393 native sweeps. Three previously unresolved stretches
consistently favor globe, giving a combined numerical tally of 15 globe, zero flat
and 38 unresolved while preserving the original study.

The [full recovery preparation](ilvis0-position-recovery-preparation-20261013/README.md)
records all 41 original unresolved stretches and their 130 unfinished fits. If the
qualification passes, reusing its 15 primaries and three repeats leaves 115 primary
recoveries, 38 repeated-start checks and six fresh controls: 159 starts, capped at
95,718 native sweeps. The ceiling estimate is 51–76 hours on two threads. Selection
uses original completion status and UTC order, never model costs. This is metadata
preparation; the qualified trial now supports the separately frozen
[remaining-stretch recovery](ilvis0-position-recovery-20261013/README.md).
Each newly complete stretch must also pass its repeat check and fresh controls.

The wider run completed all 159 starts and 22,355 sweeps: 117 fits passed, including
all six fresh controls. Eighteen original unfinished stretches pass their complete
comparison and repeat, bringing the combined tally to 30 globe, zero flat and 23
unresolved. The earlier 15/0/38 tally above describes the subset stage, not current findings.
The completed freeze permits no retries or use of its unused allowance.

The next priority is **overlapping flight legs recorded by
two instruments when one comparison finishes and the other does not**. Start with
the 24 October 2009 IMU8/IMU21 leg and the 26 September / 7 October 2015
loaner/DMS legs. Use the same shared UTC interval, compare per-axis raw and
motion-context rate differences, and inspect model-specific costs and stopping reasons.
Keep different recorders separate; an unfinished result is not an opposing shape finding.
The [analytics export](ilvis0-position-stability-trial-20261013/ANALYTICS.md) records
these pairs and descriptive measurements without new fits. A subsequent numerical
comparison needs its own finite freeze; the completed recovery allowance stays closed.

The [saved paired-recording diagnosis](ilvis0-shared-leg-diagnosis-20261014/README.md)
finds six overlapping recorder pairs with different completion outcomes. Each of
the three priority pairs has one failed primary fit: two miss only the relative-cost
stability check, while the third misses the vertical position-stability check.
All three pass endpoint stationarity. Saved agreement does not relabel a failure.
The [bounded endpoint diagnostic](ilvis0-shared-leg-probes-20261014/PLAN.md) checks
the three failed endpoints and their three successful-recorder counterparts with
sixty native evaluations maximum and zero optimizer starts. It compares repeated
predictions, value/derivative implementation agreement, and full/half/quarter local
corrections before any new fit policy is considered.
It completed all sixty evaluations. Repeated coordinates were identical, and the
value and tangent implementations agreed within 0.00025 micrometres across all
evaluated points. Smaller corrections pass the measured probe checks at two failed
endpoints; the October 2015 DMS endpoint still fails the cost check. A neighboring
originally completed loaner endpoint also fails the newer full-correction check.
The [completed probe report](ilvis0-shared-leg-probes-20261014/README.md) retains
these observations without changing any disposition. The next test concerns
derivative accuracy and integration precision in weak calibration directions,
rather than further attempts under the unchanged stopping procedure.

The [wider-arithmetic diagnostic](ilvis0-shared-leg-precision-20261014/README.md)
now compares the same six endpoints at identical parameters and frozen local
corrections. Its maximum is 84 native evaluations with zero optimizer starts.
The new kernel passed exact-motion and derivative controls before archived use;
it retains the equations, bounds and packet-clock branches. A completion watcher
publishes the sealed report and then runs six exact-motion solver controls after
the native job releases its four-thread allocation. Any subsequent observed-fit
qualification still needs its own finite freeze; no old failed fit is promoted.
That comparison is now complete: five of six full probes pass with wider arithmetic,
including both cost-only failures; the September disc vertical failure remains.
Eleven arithmetic/derivative controls and six exact-motion solver controls passed.
The [paired qualification trial](ilvis0-paired-precision-trial-20261014/README.md)
passed all sixteen fits, including both controls and perturbed repeats, in 129
sweeps. Both previously unresolved targets now favor globe, bringing current
findings to **32 globe preferences, zero flat and 21 unresolved**.

The [separate cost-only recovery](ilvis0-cost-precision-recovery-20261014/README.md)
completed all 86 starts in 891 sweeps, passing 83 fits, both controls and all twelve
repeats. Nine more stretches have complete comparisons, bringing findings to
**41 globe preferences, zero flat and 12 unresolved**. The other three primary fits
exhausted the forty-evaluation allowance. The next bounded continuation preserves
models and gates while allowing up to 200 evaluations and fresh repeats/controls.
The nine earlier stationarity/position-failure stretches require their own assessment.
Neither prior freeze may restart or reuse its unused allowance.

Minimum solver qualification supports this recovery sequence. Additional clock,
calibration, covariance, measurement-contribution and independent-flight studies
can be revisited afterward; they are not prerequisites for attempting numerical
recovery. No new numerical allowance is implied by this roadmap.

## Priority and scope

The [matched trial](ilvis0-solver-trial-20261010/RESULTS.md) is now complete: 10/12 fits
converged versus 11/12 in its baseline. The control kept its globe/rotation preference;
the other stretch remains unresolved. The
[saved-fit calibration/adequacy audit](ilvis0-calibration-audit-20261010/README.md) now
reports signed limits, parameter associations, local weak directions and residual RMS
for all 318 first-pass and 12 trial fits. The
[two-recording residual diagnostic](ilvis0-residual-diagnostic-20261010/README.md) has
completed 24 saved-parameter predictions with no refits. It reproduces baseline errors,
finds temporal correlation after whitening, and exposes a large vertical clock effect.
Full-flight solver qualification remains planned; the completed calibration comparisons
below examine matched alternatives.
The [software qualification matrix](ilvis0-solver-qualification-20261010/README.md) now
passes 34/34 predefined starts, including short independently generated IMU/GPS controls.
It qualifies those small cases, not full archival optimization. The
[six-start clock comparison](ilvis0-clock-trial-20261010/README.md) has completed with
all six fits converged. Reoptimization under packet-header timing restores the control's
rotating-globe vertical error to about 0.70 m and preserves its globe/rotation preference.
Z-axis gain and offset still reach their bounds. The completed control's nominal-clock
references remain unchanged; calibration sensitivity is the next unresolved comparison.
The [saved clock/calibration audit](ilvis0-clock-calibration-audit-20261011/README.md)
shows that gravity correction leaves its limit while Z gain and offset remain pinned.
Its [prepared sensitivity plan](ilvis0-clock-calibration-audit-20261011/CALIBRATION_PLAN.md)
isolates each Z correction with matched zero-anchor ablations; those are diagnostic
references, not asserted factory calibrations. The separately frozen
[12-fit calibration comparison](ilvis0-calibration-trial-20261011/README.md) has
completed: 11 fits converged. Gain-zero preserves globe/rotation preference under
both processing cases; offset-zero remains incomplete because one still-globe fit
exhausted its allowance. All four rotating-globe fits retain close track errors.
No retries are authorized. The [retrospective prediction trial](ilvis0-prediction-trial-20261011/RESULTS.md)
has completed with five of six fits converged. In its fully completed processing case,
horizontal prediction RMS is 2.45 m for rotating globe, 142.9 m for still globe and
166.0 m for flat disc. The second case's flat fit exhausted its allowance, leaving the
combined comparison unresolved. This recording had already been examined in full;
the split does not turn it into unseen-data confirmation.

The [saved prediction audit](ilvis0-prediction-audit-20261011/README.md) now shows
where prediction errors grow and how calibration changes with the fitting window.
Z gain switches from −2% in whole-stretch fits to +2% in training-only fits under
both processing cases; gravity correction returns to its limit. The
[solver-scaling comparison](ilvis0-unit-scale-trial-20261011/README.md) completed
five of six fits. The sixth reached a much smaller projected gradient but did not
satisfy its stopping rule; it remains unfinished. The
[verified-stopping comparison](ilvis0-verified-stop-trial-20261011/RESULTS.md)
also completed only five of six fits and did not qualify. The
[saved failure audit](ilvis0-verified-stop-diagnosis-20261011/README.md) identifies a
bounded residual-step probe 1.55 times its stability limit. The next work is independent
clock/calibration controls and review of numerical strategies.
Predeclared prediction checks on two other recordings follow only if the numerical
method qualifies and receive their own allowance. The
[solver and replication plan](ilvis0-prediction-audit-20261011/NEXT_PLAN.md) preserves
those records and criteria. The six-fit allowance is spent and permits no retries.
The two-recording replication still needs its own finite allowance,
and calibration robustness remains a separate check.

The [joint Z calibration audit](ilvis0-z-profile-audit-20261011/README.md) now reports
27/27 converged fits on the control. All nine fixed gain/offset pairs preserve globe
preference, then the specified background-field preference. The preferred cost varies
2.58%, with 0–1 remaining parameters at limits. Its advantage does not depend on
the two extreme Z corrections, but this does not determine factory calibration.
Two separately frozen grids now test
[profiled upstream removal](ilvis0-z-profile-removal-20261011/README.md) and the
[earliest predeclared other recording](ilvis0-z-profile-replication-20261011/README.md).
Both are now complete: removal converged 27/27 fits; the other recording converged
25/27, with seven complete globe preferences and two unresolved nodes. Each spent
its 27-start allowance. The next saved-only audit compares remaining calibration
limits and weak directions and examines the two stopping failures. The second grid
checks whole-stretch robustness; held-out prediction replication remains deferred.

The [saved follow-up audit](ilvis0-z-followup-audit-20261012/README.md) now compares
all 81 grid fits and checks 243 epoch residual series against their saved costs and RMS.
Both unfinished fits pass saved stationarity but exhausted the solver allowance without
reported success; neither is relabeled. Preferred-model costs barely change when removal
is profiled, with fitted removal effectively zero on the control. No new observed
starts are included in this audit.

The [residual covariance audit](ilvis0-residual-covariance-20261012/README.md) now
reports dense lag curves, cross-axis matrices and spectra for all 81 saved fits.
On October 5, the preferred model's vertical innovations retain a 60-second correlation
of about 0.27, with about 68% of spectral power at periods of at least a minute;
September 24 shows less slow dependence. These are two recordings, not independent
calibration-grid replications. The [shared error-model plan](ilvis0-residual-covariance-20261012/ERROR_MODEL_PLAN.md)
sets out common cross-axis and correlated-error terms, development-only estimation and
blocked prediction checks. The [covariance software controls](ilvis0-error-model-controls-20261012/README.md)
now pass all 35 checks: irregular times, cross-axis and coordinate transformations,
whitening, fixed drift anchors and conditional prediction across a split. They use
known covariance and residual mean; they do not include fitted-parameter uncertainty.
The [training/prediction controls](ilvis0-error-training-controls-20261012/README.md)
now pass 26 checks for training-only restricted-likelihood covariance selection,
linear-parameter uncertainty and covariance-choice sensitivity. They do not integrate
covariance-parameter uncertainty or handle the NASA fits' nonlinear active bounds.
A bounded observed comparison must specify those treatments before launch and
still requires qualification and a finite allowance.
The [nonlinear/boundary controls](ilvis0-nonlinear-uncertainty-controls-20261012/README.md)
now pass 25 geometry checks and an independent estimator-distribution check. They
retain active parameters, identify deficient directions and preserve disconnected
sampled support. They do not qualify NASA confidence intervals. The
[preparation plan](ilvis0-nonlinear-uncertainty-controls-20261012/NEXT_PLAN.md)
now has a [control-tested native adapter](ilvis0-native-uncertainty-controls-20261012/README.md).
Six independent geographic controls verify all 27 columns with 348 native software
sweeps and no archive reads or observed fits. The [costed comparison preparation](ilvis0-prediction-covariance-preparation-20261012/README.md)
now specifies 12 October 5 training/prediction fits under shared 10- and 300-second
correlation assumptions, capped at 3,060 native sweeps with no retries. Its estimated
ceiling is 154–172 minutes. The [durable launcher](ilvis0-prediction-covariance-20261012/README.md)
now passes 39 worker, planning and native controls. Its separate freeze requires
explicit approval of the finite allowance. Its approved 12-start comparison has
completed with 10 converged fits; its combined hierarchy remains unresolved.
That allowance does not authorize the separate recovery study.

| Order | Work | What can happen without new observed fits? | Deliverable |
|---|---|---|---|
| P0 | Recover the 41 numerically incomplete stretches | Test the separately prepared rectangular solver on the frozen representative failures and completed control. | Qualified numerical method, then a separately budgeted recovery study on all 41. |
| Deferred | Explain integration timing and joint Z-axis calibration | Preserve completed clock tests, gain–bias grids and weak-direction audits. | Further physically justified clock/calibration tests after recovery. |
| Deferred | Model residual dependence and assess prediction quality | Preserve covariance audits and the active comparison's results. | Calibrated predictive adequacy and uncertainty checks. |
| Deferred | Isolate what the inertial measurements contribute | Preserve the planned channel and receiver-metric controls. | Measurement-contribution study with matched assumptions. |
| Deferred | Test independent-flight generality | Keep recording dependence and provenance explicit. | Predeclared prediction replication across independent flights. |
| Parallel, lower priority | Seek exact device and processing records | Continue the existing inquiry; record what each source actually establishes. | Better-supported assumptions where information becomes available. |
| Follow-on | Measure the background rotation field | Prepare the estimator design and separation checks after current numerical work is reviewed. | Freely estimated field before interpretation of its cause. |

The [focused diagnostic plan](ILVIS0_DIAGNOSTIC_PLAN.md) incorporates the October 11
review, identifies tests already completed, and specifies the remaining clock,
calibration, covariance and measurement-contribution work. The priorities above guide
the next studies; they do not interrupt the approved numerical trial or expand the corpus.

This roadmap authorizes no new observed starts, synthetic campaigns, deletion, resumption
of completed studies or production promotion. The verified-stopping trial is complete;
its six-start allowance is spent, with no retries. Any new numerical work needs a separately identified
configuration and finite approved allowance. Future jobs share a four-thread total
budget through the launch guard; active and historical freezes retain their original settings.

## 1. Qualify numerical completion

Review the [matched solver trial](ilvis0-solver-trial-20261010/README.md) against the
preserved baseline: objective values, stationarity, stability, boundary behavior and
predicted observations. A materially worse completed control or unexplained change in
ranking needs investigation before expansion. Do not simply promote the 42 old
budget-stopped fits that happened to pass stationarity.

Add bounded qualification controls generated independently of the fitting kernel:
known interior and boundary optima, transport-only and background-rotation inputs,
nearly redundant parameters, timing perturbations, and several deterministic seeded
starting points. The existing analytic solver tests are a start, not an independent
end-to-end IMU/GPS qualification. Check objective agreement and prediction recovery;
require parameter recovery only for combinations the controls identify. Count every
start and evaluation. Multi-start agreement improves confidence but does not prove a
global optimum. Distinguish a converged but poor flat fit from an unfinished flat fit.

The completed software matrix already includes short independently generated IMU/GPS
controls. Extend that evidence to realistic integration lengths, both clock conventions,
coupled gain/offset errors, near-boundary optima and poor initial states. Compare two
numerical strategies over the same feasible region. A larger evaluation-budget sensitivity
is a separate future freeze, not permission to retry or relabel the original failures.

## 2. Explain calibration-boundary saturation

The first pass reached the Z-axis gyro-gain limit in **304/318 fits** and its offset
limit in **294/318**. The median completed fit had 15 parameters at a limit. A constrained
optimum can legitimately sit on a boundary; this frequency warrants its own audit.

For every parameter, report its physical estimate, normalized distance to each limit,
upper/lower boundary counts, model/case dependence and associations with clock, mounting,
speed and latitude. Examine Z-axis gain and offset together. Across-fit correlations of
estimates describe the archive; they are not within-fit parameter uncertainties. Use
projected gradients and available Jacobian singular vectors to examine local trade-offs.
The baseline saved singular values alone; do not pretend it contains those vectors.

The completed zero-gain and zero-offset tests remove one correction at a time. The first
joint grid maps combined sensitivity under header timing and no removal, preserving
gradients, remaining limits and weak directions. The next two approved grids test
the other processing assumption and another preselected recording, keeping remaining
bounds unchanged for all three models. Further clock grids need a separate allowance. Plot feasible
limits, fitted points, unfinished grid points and cost valleys. Check whether those
valleys move with clock convention. Keep this separate from an absolute calibration
estimate: a shallow valley can preserve a model preference while leaving its calibration
poorly identified. Grid size and start allowances must be costed before approval.

Specify a **small calibration sensitivity matrix before new fits**, justified by published
survey-system performance and the physical meaning of each error. Separate constant
offset, gain error and changing drift. Vary the suspect gain/offset limits in controlled
steps; hold other assumptions fixed, then test only a justified interaction. Apply every
case equally to rotating globe, still globe and flat disc. Preserve preferences, failures,
residuals and boundary behavior whether or not they favor globe.

Success means either explaining why a boundary is physically appropriate or showing a
stable preference under defensible alternatives without systematic unexplained extremes.
Do not add unrestricted time-varying bias just to improve residuals or choose limits that
produce a desired shape. Exact per-unit certificates are not required to run these tests.

## 3. Assess absolute model adequacy

Every completed fit should report physical horizontal/vertical residuals, whitened RMS,
residual quantiles/outliers and temporal dependence. Whitened residuals are errors scaled
using the declared GPS covariance. Test their distribution and autocorrelation against
what that covariance predicts; a small relative model cost does not establish that the
covariance or preferred model is adequate.

Plot residuals against receiver speed, latitude, height, elapsed time and independently
available maneuver indicators. Use measured temperature only if a documented channel
exists. Elapsed time or aircraft movement must not be relabeled sensor temperature.
Store epoch-level residuals and weights in a new diagnostic artifact if the old outputs
lack them; generating predictions still has a numerical cost even without optimization.

The completed two-recording diagnostic now stores per-epoch errors under both clocks and
both covariance assumptions. Its nominal rotating-globe residuals are small but retain
lag-one correlations of roughly 0.42–0.76. Packet-header timing raises vertical RMS
to approximately 9.2–9.4 m without changing fitted parameters. These findings prioritize
the clock comparison; they neither establish a calibrated adequacy failure nor replace
held-out prediction checks. Speed/course covariates in this diagnostic are coordinate-derived
proxies under a reference globe metric, not recorded VTG measurements or independent evidence.

The completed [covariance audit](ilvis0-residual-covariance-20261012/README.md)
extends the saved grid epochs through 60 lags, with cross-axis covariance and
low-frequency power, retaining actual time separations and cadence limitations.
Irregular records receive no spectrum or resampling. These are fitted navigation errors containing receiver error,
inertial error and model mismatch; they cannot alone identify receiver noise. Compare
available fix-quality and precision channels without treating those indicators as measured
error variance; the selected saved epochs lack those fields. Estimate and seal a shared covariance alternative on development or
training observations before evaluating later predictions. Do not choose a different
covariance for each physical model or calibrate a significance threshold on its own
in-sample residuals.

Retain the whole-stretch fit as the primary analysis. Existing fixed-parameter 4–10-minute
section checks remain useful, but **are not held-out validation**: the parameters saw
those observations. A genuine blocked prediction check fits calibration/initialization
using training receiver observations only and evaluates withheld receiver positions using
the original IMU increments. Account for correlated GPS errors across the split and fitted
parameter uncertainty. When a short stretch cannot support a meaningful split, report
that limitation and use separate-flight validation; do not invent independent trials.

Develop and validate an absolute-fit criterion before it can authorize positive scientific
support. Account for fitted parameters, active bounds, correlated errors and solver failures;
do not assume a textbook chi-square cutoff applies automatically. Calibration must cover
the full hierarchy, including the minimum of the two globe costs and the selection process.

Public reporting should distinguish:

- **Preferred model:** the complete matched comparison has a lower cost.
- **Adequacy not established:** required absolute-fit checks are missing or unvalidated.
- **Preferred but inadequate:** the relative winner fails established fit-quality checks.
- **Validated support:** numerical, adequacy, robustness and statistical decision checks pass.

These future labels do not retrospectively change the current findings. The existing
production significance gate stays intact until the additional checks are validated.

## 4. Compare timing and receiver-coordinate assumptions

The [selected-packet clock audit](ilvis0-clock-audit-20261011/README.md) now reproduces
both frozen recordings, including both time tags and native provenance. UTC elapsed
time differs from nominal by about 22 ppm. Independent physical controls demonstrate
how this can accumulate into substantial height error and trade off with gravity;
they do not identify the NASA increment period or reproduce the full fitted calibration
shift. No new observed fits or native predictions were made. The
[coupled three-dimensional controls](ilvis0-coupled-controls-20261011/README.md) now
recover known motion and demonstrate both packet-endpoint compensation and its loss
under independent observation times. They check the Python integration primitive and
known-reference linear calibration. The separate
[geographic controls](ilvis0-geographic-controls-20261011/README.md) extend testing
through both native kernels and nonlinear solvers, with independent receiver times and
six free calibration/initialization/latency parameters under all three true models.
Their report retains every outcome. Full nuisance freedom and long-record conditioning
still need qualification before observed profiles.

All 24 geographic fits passed the predefined convergence/prediction checks. Their
[calibration audit](ilvis0-geographic-controls-20261011/CALIBRATION.md) shows why this
is insufficient: micrometre track errors coexist with up to 0.647°/hour Z offset error
in the short synthetic tracks, and all 12 near-boundary fits reach the offset limit.
The completed [interval controls](ilvis0-interval-controls-20261011/FINDINGS.md)
separate those effects: all nine new fits passed, offset errors shrink approximately
with interval squared, and added roll reduces the remaining error by another factor
of 34–42. This identifies a numerical/geometry mechanism in the synthetic controls,
without establishing the NASA boundary mechanism. The
[original-rate correction comparison](ilvis0-compensation-controls-20261011/FINDINGS.md)
has now completed: all nine new fits passed, and combined coning/rotating-force
corrections reduce offset error to at most 0.000377°/hour across the three supplied
truths. Both globe controls recover within 0.000011°/hour. Conditioning remains weak;
these noise-free, six-parameter controls do not qualify noisy or full archival fits.
The [latitude/convention extension](ilvis0-latitude-controls-20261011/FINDINGS.md)
has also completed: all 24 fits at ±45° pass, with offset errors below 0.00079°/hour
and no calibration limits reached. Opposed starts and roll/unequal timing retain
the improvement. Correcting already-compensated inputs instead introduces error.
A [six-fit NASA integration comparison](ilvis0-integration-trial-20261011/README.md)
has completed with unchanged header timing, bounds and solver: four fits converged
and both zero-field globe fits exhausted their budgets. The
[27-column derivative check](ilvis0-latitude-controls-20261011/DERIVATIVES.md) has
passed for all three candidates; global optimizer qualification remains distinct.
Do not upsample observed packets or double-correct the archive. The
[saved integration audit](ilvis0-integration-audit-20261011/README.md) preserves the
original findings and identifies no improvement in Z boundary saturation. Its
[staged profile plan](ilvis0-integration-audit-20261011/PROFILE_PLAN.md) proposes
27 fixed gain/offset comparisons, roughly 6–7 hours, under original integration
and one processing case first. Implement/test its worker and obtain a separate
finite allowance before execution. The [profile worker](ilvis0-z-profile-20261011/README.md)
now implements fixed-coordinate reoptimization, final derivative capture and recovery;
preparation starts no fits. The integration alternative is not ready for corpus rollout.

The control's matched reoptimized clock comparison is complete: all six fits converged,
the close rotating-globe fit returned, and globe/rotation preference survived. It shows
that calibration can absorb much of the fixed-parameter clock effect; it does not establish
the physically correct integration interval. Z gain and offset remain at their limits.

First audit packet timestamp quantization, interval distributions, cumulative elapsed-time
drift, rate changes and discontinuities, separately from the period represented by each
increment. Compare nominal timing with header timing without selecting the convention
that gives the preferred model its smallest cost. Use independent packet-jitter controls
and available decoder-validation channels to investigate the distinction. Group1 remains
fused navigation and supplies no independent Earth-model evidence. Then a separately
frozen extension can test the other preselected recording and the joint calibration
profiles under both clocks. Report costs, ranking, completion, calibration and prediction
quality, including incompatible or inconclusive timing evidence.

Then compare full three-dimensional receiver positions with horizontal-only observations,
an altitude-only diagnostic and justified height/geoid perturbations. Preserve original
reported heights and geoid separations. Clearly identify which coordinates enter the
objective, initialization and motion screening. Removing altitude from the objective
alone does not mean it disappeared from the complete procedure. Check identifiability
after each ablation; an insufficient observation set cannot supply a positive conclusion.

Transform covariance consistently with any coordinate representation. Equivalent
representations of the same physical observations should agree numerically; do not
compare arbitrary coordinate units as if they carried equal information. For an axis
ablation, use its appropriate covariance rather than dropping components after joint
whitening. Receiver latitude/longitude remain outputs of a geodetic navigation system;
these tests isolate their influence, not replace them with raw GNSS ranges. Raw ranges
are a possible later extension, not a blocker for the present archive study.

Applanix V6 section 3.3.2.1 documents Group 10001 as primary-receiver output.
The planned versioned supplement will retain per-file receiver-type codes, original
NMEA identifiers, stream hashes and historical version/layout evidence.
Receiver output is distinct from fused Group 1 navigation; that source distinction
does not establish independence of coordinate assumptions. See
[the provenance record](ILVIS0.md#measurement-provenance-and-independence).

The deferred measurement-contribution study separates gyro increments, acceleration increments,
gravity and coordinate metric. Include a receiver-constrained gyro prediction where its
frame and attitude assumptions can be stated explicitly. An ablation must define its
replacement constraints and initialization, not silently supply missing gyros from fused
attitude. Check whether non-gyro inputs can reproduce the distinction under comparable
freedom. Report interacting channels and lost identifiability rather than an invented
percentage of evidence attributable to one sensor. The original measurements and primary
comparison remain unchanged.

Stage these comparisons rather than immediately multiplying every timing, calibration
and coordinate option into a large grid. Freeze each small matrix and its compute budget
before fitting, and add combinations only when earlier diagnostics justify them.

## 5. Account for completion selection and dependence

Report completion by model: rotating globe **43/106**, still globe **73/106**, flat disc
**72/106**. Analyze its relationship to pre-fit observables: duration, latitude, ground
speed, heading evolution, recorded IMU type and installation signature. Keep fitted
Jacobian conditioning in a separate numerical diagnostic; it is not an independent
pre-fit observable. With only 53 stretches, prefer a small descriptive analysis to an
overfitted prediction model. Do not select new intervals by whichever model finishes.

Build a grouping ledger using verified dates, platform information, time overlap, source
aliases and installation continuity. Distinguish a POS system identifier from a physical
IMU serial number. Where actual flight or device identity is uncertain, record that and
use conservative grouping. Several stretches or simultaneous IMU streams from one flight
must not become several independent confirmations. Hold out whole supported flight or
installation groups for replication; never randomly split overlapping samples.

Joint calibration across stretches is a later useful test **only where installation
continuity is supported**. Matching configuration bytes alone do not justify it. Model
appropriate temporal changes equally for every candidate and charge its added complexity.
Manufacturer replies can improve that support without holding up the other audits.

## Rotation-field follow-on and publication

The [saved solver diagnosis](ilvis0-solver-diagnosis-20261011/README.md) separates the
remaining numerical stopping issue from calibration ambiguity. A verified-stopping
candidate passed cheap known-optimum and false-stop controls, but its completed six-fit
airborne comparison did not qualify. Later actual-position qualification passed its
observed control and repeat checks, recovering three complete globe comparisons.
The [wider recovery](ilvis0-position-recovery-20261013/README.md) is complete, yielding
30 globe preferences, none for flat and 23 unresolved stretches at that stage. The subsequent
paired wider-arithmetic trial added two complete comparisons; the cost-only recovery
adds nine more. Current findings are 41 globe preferences, zero flat and 12 unresolved. Preserve the original 12 resolved and 41 unresolved
results alongside new recovery evidence; software controls alone do not relabel them.

The [rotation-field proposal](ROTATION_FIELD.md) remains separate: fit a retained
background vector freely and examine latitude/altitude/velocity dependence. Report its
measured properties without assigning a physical cause. Competing causal explanations
need distinguishable quantitative predictions to be tested with this archive.
It will reuse the numerical, adequacy and dependence checks above. It need
not wait for an exact hardware identification, but unknown upstream subtraction must
not be fitted as though it were independent of an unknown original field strength.

Before field fitting, audit rank using the archive's actual latitude, heading and
supported installation groups. Test the columns for north amplitude, east component
and vertical amplitude against installation-specific gyro offsets and upstream removal.
Report weak combinations and coverage; configuration similarity alone does not establish
shared calibration. This geometry check precedes fitting a common magnitude or testing
solar versus sidereal rate.

Its [precision stage](ROTATION_FIELD.md#precision-stage-sidereal-versus-solar-rate) will
also ask whether the freely measured magnitude distinguishes **15.0000°/hour** from
**15.0411°/hour**. First establish the field's direction and latitude pattern; then use a
separately selected longer-record inventory, shared calibration only within supported
installation epochs, and whole-flight held-out checks. Refit nuisance parameters when
profiling both rates. Gain, clock scale and unknown upstream subtraction can remain
indistinguishable from a change in magnitude, so longer recordings alone do not settle
the question. Report unresolved cases explicitly. This tests the period, rather than
absolute astronomical phase, and requires a separately approved bounded numerical trial.

Publish methods and empirical conclusions at the level actually supported. A methodological
paper can describe the inverse-navigation framework and verified controls even when many
real fits remain unfinished. Stronger empirical claims require adequate, robust comparisons
and genuinely independent replication. Continue preserving original increments, receiver
observations, selection, failures, source/environment hashes and complete reporting receipts.
Keep consumer-IMU development secondary; it does not resolve these archival questions.


## Secondary branch: stationary consumer crowdsourcing

The passenger-flight proposal is superseded by the [stationary A/B experiment](STATIONARY.md).
Collection now uses a solid level support, a marked horizontal axis and repeated same-face
180° reversals. Aircraft identity and flight dashboards are removed from the active app flow.
Historical aircraft simulations and frozen research remain preserved.

The signed-rate diagnostic is implemented and does not use latitude or an expected amplitude.
Next priorities are independent slow-turn response tests, sub-count sensitivity,
temperature/stability and reversal/alignment controls, then calibrated uncertainty.
Only after sealing per-recording methods should a separate population estimator fit
the latitude curve, preserving instrument/day/site dependence and all failures.
The ground experiment neither replaces NASA analysis nor inherits its thresholds.
