# Analysis roadmap

## Where the project stands

<!-- current-status:start -->
**53 globe preferences, 0 flat preferences, 0 unresolved** among 53 preselected stretches.
See the [verified current status](CURRENT_STATUS.md) for coverage, background-field comparisons and the supporting result records. All selected comparisons have passed their required numerical checks.
<!-- current-status:end -->

The main model comparison is finished. The current priority is to check how
well the models predict measurements that were left out of the fit.

An **IMU (inertial measurement unit)** contains gyroscopes that measure turning
and accelerometers that measure specific force. The analysis combines those
records with receiver positions to reconstruct the aircraft's motion.

The 53 stretches favor globe geometry and the model with a specified background
rotation signal. These are completed model comparisons. Statistical confidence,
prediction accuracy and independence between recordings still need testing.

The latest [96-recording generated whole-period check](prediction-simultaneous-law-family-v2/RESULT.md)
closed every task. Both intervals covered every later coordinate in its 92
scored recordings; four tasks stopped at the original time limit. Those four
count as failures, so the 5% coverage gate failed. Observed-flight prediction
intervals remain unqualified. The next method step is a separately frozen
runtime and coverage check, without rerunning sealed failures.

## Next: test predictions on unused measurements

The [revised prediction protocol](PREDICTION_VALIDATION.md) separates a practical
prediction comparison from formal uncertainty certification. First qualify the
training-only fitting and prediction pipeline on known-answer controls. Then fit
earlier observations in a small, metadata-selected archival pilot and score
later positions without using them to adjust the answer.

Preserve the original physical bounds and compare all three candidates under
matched assumptions. Use predeclared starts, choose primaries by training cost
only, and report every failure. Show horizontal and height errors together.
Differences between repeated predictions are sensitivity evidence, not confidence
intervals. Actual error-law assessment and calibrated significance remain open.

The [completed prediction pilot](ilvis0-retrospective-prediction-pilot-v2/INTERPRETATION.md)
fully compares one recording across both clocks and both processing assumptions:
later horizontal RMS is 0.84–1.13 m for specified-field globe, about 496 m for
zero-field globe and 793 m for disc. Two other recordings retain numerical or
accuracy failures. Broader validation remains open. These are retrospective
development tests; reserved ESA groups stay protected.
The [saved receiver-only control](receiver-only-forecast-baseline/INTERPRETATION.md)
uses the same three withheld periods with no IMU input. Its constant-velocity
horizontal errors are 87–351 m. A [spherical-path receiver control](receiver-only-geodesic-control/INTERPRETATION.md)
reduces those errors to 33–189 m. On the northern complete comparison, the
IMU forecasts remain much closer than either fixed receiver-only rule. A
gyro-specific channel ablation and calibrated adequacy remain open.

The [saved receiver-precision comparison](receiver-precision-holdout/README.md)
matches every pilot epoch to the same receiver's precision report. Of 36
settings, 28 have a numerically qualified start chosen from earlier data only.
The specified-field globe passes the pilot's uncalibrated accuracy screen in
seven of its nine qualified settings, but even its median later errors are
about four times the receiver-reported horizontal precision and eleven times
the height precision. The receiver estimates are not a full prediction-error
budget; observed-aircraft adequacy and uncertainty calibration remain open.
Across the nine qualified specified-field globe settings, a straight time
trend explains a median 95.7–97.4% of centered later-error variation by axis.
This describes already observed errors; the slope was not known from training.
The [fixed training-only drift check](prediction-drift-control/README.md)
tests that missing step. Its straight-line correction worsens seven of nine
qualified specified-field globe forecasts and improves the alternatives,
which still miss by hundreds of metres. A deterministic residual line is not
a qualified replacement for the combined error model.
The [next error-law gate](PREDICTION_ERROR_LAW_PLAN.md) first tests
identification and later-error coverage on known-answer controls. Any adjustable
quantities must come from earlier observations; protected confirmation groups
remain closed until the method and flight groups are frozen.
A twelve-case short native aircraft matrix now completes fits and saves
separate physical-position and future-receiver uncertainty targets before
later truth. It covers three models, both processing cases and two synthetic
IMU input-error forms. The source-bound clock/calibration matrix and coverage
test are next.
A separate exact-period 200 Hz generated path now passes native training under
both declared clocks. A separate deterministic packet-time disturbance keeps
the generated IMU increments and receiver reports fixed; the two native
forecasts then differ. The actual archive clock is not established by this
software control.
The [24-case generated-aircraft uncertainty check](bounded-calibration-prediction/NONLINEAR_RESULT.md)
is complete. All 24 technical cases and withheld-position accuracy screens
pass; one fit fails its numerical stopping check, so the combined gate is
23/24. The bounded intervals contain every tested coordinate but are broad;
this development matrix does not establish calibrated nonlinear coverage.
The [saved diagnosis](bounded-calibration-prediction/NONLINEAR_DIAGNOSIS.md)
shows its proposed timing step crosses packet boundaries for all 79 training
queries. A short clean control finds negligible error across such a boundary,
so the long noisy case received a [finite targeted timing probe](bounded-calibration-prediction/TIMING_PROBE_RESULT.md).
Its sealed values show that timing-only changes follow the tangent; the
coupled calibration/timing direction remains unresolved, and the probe's
technical wrapper is terminal. The separate
[48-case independent-seed check](bounded-calibration-prediction/INDEPENDENT_SEEDS_RESULT.md)
now passes every numerical and withheld-position gate on two new noise draws
per condition. Its broad bounds contain every tested coordinate. It does not
calibrate 95% coverage or establish an observed-aircraft error claim.
The [saved ESA precision check](esa-prediction-error-scale/README.md) matches
all 22 available forecasts to the receiver's reported uncertainty and retains
the two original fit failures. Even the specified-field globe forecasts exceed
receiver precision by large factors. Receiver precision alone cannot serve as
the uncertainty of an IMU-based aircraft forecast; this check is descriptive,
not a calibrated detection.

Global interval certification is now a separate research track. Its earlier
bounds and counterexamples remain published, with unchanged failure labels and
width targets. The [completed training-bound study](ilvis0-dense-physical-bounds/INTERPRETATION.md)
preserved 348 reports, but none of its six cases qualified. No further bound
expansion precedes the revised prediction sequence.

[Revised method and safeguards](PREDICTION_VALIDATION.md) ·
[Error assumptions](PREDICTION_ERROR_ASSUMPTIONS.md) · [Study history](STUDIES.md).

## Current phase and finish line

**An earlier generated decision-threshold validation is complete.** Calibration
set a fixed error limit for that separate simulated decision test. This does
not qualify the newer whole-period prediction intervals described above.
A reboot interrupted the original validation after 3,750 saved fits; its
complete-cohort rule cannot be met. A separate, reboot-resumable continuation
completed the other 594 fits. The independently replayed
[combined audit](prediction-validation-continuation/README.md) verifies all
4,344 fits across 181 preselected simulated cases. No case exceeded the limit;
the one-sided 95% failure upper bound is 1.64%, below the declared 5% target.
This validates the procedure under its simulated conditions. Aircraft error
coverage and Earth-model significance require further evidence.
The next gate is to test physical adequacy and prediction on preselected,
independent aircraft groups, with the receiver-error assumptions fixed before
using protected confirmation recordings. The generated-data threshold does not
transfer to observed aircraft by itself.
The [48-case generated-aircraft integration matrix](prediction-aircraft-error-integration/RESULT.md)
passes every technical pipeline check. Its deliberately short fits yield no
numerically converged or physically passing predictions, so it supplies no
uncertainty-coverage qualification. A longer, independently seeded known-answer
study must qualify training-only error estimation and prediction coverage.
The candidate-law comparison helper now enforces identical earlier IMU and
receiver measurements and records numerical score rankings without making a
scientific selection. Its four local checks pass. A separately frozen longer
generated-aircraft study still has to fit both laws to each *same* recording,
then test convergence and withheld coverage.

A [receiver-only binary inventory](ilvis0-trimble-position-precision/recorded-inventory/README.md)
now has saved outcomes for all 53 selected recording files. Fifty-two contain
accepted, checksummed position-precision reports; one fails the strict receiver
decoder. Those reports are receiver estimates. Their real error and time
correlation must be checked before they inform an aircraft prediction threshold.
The [paired-receiver study](ilvis0-receiver-overlap/recorded-study/README.md)
then completes all eleven usable overlaps. It measures close, strongly
correlated differences, but shared GNSS error remains unknown. It therefore
does not qualify the aircraft prediction-error law.

The detailed record below explains the development steps and failed releases
that led to this run. Those results remain separate from the current validation.

**The [coordinate-precision controls are complete](coordinate-precision-controls/INTERPRETATION.md).**
Compensation passes all six known-answer cases, compared with three for the
original arithmetic and four for the longitude-only alternative. The study
returns all 18 tasks in 7.13 seconds after 46 source-bound software checks.

The [full saved-point check](saved-point-coordinate-precision/INTERPRETATION.md)
now passes all 315 derivative comparisons and all four stopping probes under
the original limits. It finishes in 27.2 minutes using 650 evaluations, after
99 software checks. The earlier matched diagnostic isolated the timing issue;
compensated accumulation also resolves the weak gyro-column precision problem.
The original labels, thresholds, observations and numerical environment stay
fixed. [Optimizer qualification](compensated-optimizer-qualification/INTERPRETATION.md)
now passes all 48 development fits, all 24 paired-start comparisons and all four
original input/error replays. It finishes in 30.3 minutes after 93 software checks.
The [fresh calibration release](prediction-calibration-compensated/INTERPRETATION.md)
stopped under its frozen failure rule after 909 returned starts in 9.58 hours:
904 passed, two failed numerical cost stability and three stopped cooperatively.
All 906 completed forecasts passed the fixed position-error screens. No finite
uncertainty threshold was established, so independent validation remains blocked.
Both campaigns and their unused allowances stay closed. A
[saved timing review](prediction-clock-boundary-review/README.md) verifies
that both failed points lie close to internal integration boundaries. Check
the [saved linear corrections](prediction-linear-timing-review/README.md): all
four replay, while both failures cross all 119 query boundaries and the two
successful controls cross none. Four [analytical controls](timing-kink-controls/README.md)
also show the original check can reject exact nonsmooth minima with correct
derivatives. The physical-model cause remains unproved. Check both timing branches
before a separately reviewed method revision. The [four-point diagnostic](saved-timing-boundary/INTERPRETATION.md)
now completes all 78 evaluations in 6.7 minutes. Every saved input, residual and
27-column Jacobian replays exactly; all 18 within-interval timing derivative
comparisons agree. Most full-step prediction error appears in the timing-only
movement, while timing and other calibration effects nearly cancel.
[Steps constrained to timing intervals](TIMING_CELL_STEP_PLAN.md) now pass
independent known-answer qualification. The [saved-matrix review](saved-timing-cell-proposals/INTERPRETATION.md)
now returns all 18 successful linear solves after 26 software checks. All
feasible sides and spacings agree on the failed cases' proposed boundary;
their predicted remaining improvements fall below the original cost limit.
[Physical evaluation](saved-timing-cell-native/INTERPRETATION.md) now passes
all 18 proposals under the original cost, stationarity and position-change
screens. The run uses 26 evaluations in 2.6 minutes after 103 software checks;
the largest actual position change is about 1.5 micrometres. The next gate is a
complete interval-aware optimizer qualified on independent known optima,
non-optima and repeated starts. No earlier result is relabeled. No new campaign starts
automatically. Generated-data coverage and actual flight-level confidence
remain separate gates.

The [timing-aware stopping method](TIMING_STOPPING_PLAN.md) retains the
existing fitting method and numerical limits. Its
[analytical qualification](timing-stopping-qualification/INTERPRETATION.md)
now passes all 32 fits, eight direct controls and eight start-comparison
groups, using 1,008 evaluations in 26 seconds after 161 software checks.
The [four-fit native phase finished without qualification](timing-optimizer-regression/INTERPRETATION.md).
All original inputs replay, but all four fail final cost stability despite
passing the declared forecast screens. The failed checks use distant cell
midpoints. An independent curved-minimum control reproduces that false-failure
mechanism and passes with nearest feasible anchors. The
[local timing qualification](timing-local-qualification/INTERPRETATION.md)
now passes 36 fits, eight controls and all nine starting-point comparisons in
27.5 seconds after 175 software checks. Projection alone failed sharp-corner
tests before freezing; this version uses cell midpoints clipped to the existing
local timing window. It retains every cell, nuisance coordinate and numerical
limit. The [new four-case native trial](timing-local-native-regression/INTERPRETATION.md)
passes all fits, both start comparisons and all original input replays in
10.7 minutes after 189 software checks. The [48-case matrix](timing-local-matrix/INTERPRETATION.md)
now passes all 48 fits, all 24 start comparisons and four original input replays
in 65.7 minutes after 203 software checks. This completes the declared optimizer
qualification. Next is a [separately budgeted calibration/validation release](TIMING_CALIBRATION_RELEASE_PLAN.md),
with new cohorts, a frozen method and a checked handoff. Neither closed campaign
resumes; earlier labels are preserved.
The [local-timing calibration](prediction-calibration-timing/INTERPRETATION.md)
stopped under its frozen failure rule after 348 returned starts in 6.82 hours:
344 passed numerical checks, two failed timing-cell stability and two stopped
cooperatively. All 346 completed forecasts met the position-error limits.
The independent audit establishes no calibration threshold; validation was not
launched. The [saved-baseline diagnosis](timing-linear-baseline-diagnosis/README.md)
now reproduces worsening linear proposals in both failed cases, while the
matched controls do not worsen. All four saved calculations and their charges
were checked; the result-schema rejection remains preserved. No native call or
fit was run. The [feasible-initialization revision](timing-linear-anchor-check/INTERPRETATION.md)
now passes all 24 independent convex controls and four matched saved-matrix
checks after 56 source-bound checks; 90 related software tests also pass.
The previous method fails ten of the 24 controls. The
[fresh complete-optimizer qualification](timing-feasible-optimizer-qualification/INTERPRETATION.md)
now passes all 36 known-answer fits, eight direct probes and nine starting-point
groups in 27.8 seconds after 148 software checks. The separately frozen
[six-case native regression](timing-feasible-native-regression/INTERPRETATION.md)
now passes all six fits, three start comparisons and six original-input replays
in 10.6 minutes after 338 pre-execution software checks. Its 238-source freeze
retains all columns, bounds and limits. A reporting-only metadata repair passes
339 checks without rerunning fits. The [matrix audit](timing-feasible-matrix/INTERPRETATION.md)
now accepts all 44 completed fits and 22 complete start pairs in 51.0 minutes.
Four charged starts were interrupted by a runtime reset and remain failures.
All 1,239 publication artifacts and 28 native assets verify; the archived report
replays identically. Full matrix qualification is unavailable from this run.
A [separate four-case follow-up](timing-matrix-completion/INTERPRETATION.md)
passes all four fits, both start pairs and the remaining original replay in
4.6 minutes after 364 software checks. The
[saved-only combined audit](timing-matrix-combined/README.md) now qualifies
all 48 computational cases, 24 start pairs and four original replays after
16 additional assembler checks. All 241 common execution sources and the
environment match; the interrupted study retains its original failed state.
The [latest calibration release](FEASIBLE_PREDICTION_STATUS.md) stopped after an
execution interruption, with 1,813 numerically passing fits and four interrupted
starts after 38.7 hours. All 253 sources and the numerical environment still
match. Both starts of one required setting are unavailable, so the remaining
5,359 starts are closed unused. No calibration threshold or validation follows
from this incomplete cohort. The [independent audit](prediction-calibration-feasible/INTERPRETATION.md)
confirms all 1,813 completed forecasts also pass the position-error checks.
All 42,064 publication artifact hashes verify and the archived report replays
identically. The [recovery checker](execution-recovery/README.md) passes its
61-check software suite. The [host-service lifecycle control](execution-host-service/README.md)
also passes normal submitter-exit survival. The [fresh release](HOST_PREDICTION_STATUS.md)
has completed all 7,176 fits, all passing, in 151.7 hours after 154 software
checks and independent freeze verification. Its saved-data audit and publication
replay passed, supplying a finite prediction-error threshold. Independent
validation saved 3,750 passing fits before a host reboot interrupted four
charged starts. Its frozen complete-cohort rule prevents a coverage claim;
task-level recovery must be qualified before another long-running release.
These regressions do not establish statistical coverage.
This release and its unused allowance remain closed.

Previously, **calibration stopped early; validation was not run.** The
[phase report](PREDICTION_PHASE_RESULTS.md) records 1,683 qualified fits, two
numerical failures and one interrupted start. The one permitted saved-results
review identifies the cost-stability check as the failed numerical gate.
That completed phase's finite scope was:

1. Finish the existing calibration run within its original 299-family,
   7,176-start, 120-hour allowance. Preserve early stopping and every failure.
2. Run the separate 181-family, 4,344-start validation phase only if calibration
   supplies a finite, closed and verified threshold under the same population.
   Preserve its 72-hour ceiling and predeclared acceptance rule.
3. If either phase fails, permit **one saved-results diagnosis in total**:
   at most 24 existing fit records, no new noise draws, optimizer starts or native
   calculations, one numerical thread and a ten-minute cooperative ceiling.
   This review explains the failure; it does not retune the method or retry it.
4. Audit hashes and accounting, publish the outcomes and CSV data, update the
   overview pages, and write a concise phase report with findings, limitations
   and a prioritized follow-on backlog. **Then stop for review.**

Phase completion means an accurately audited and published outcome, including
a failed or inconclusive outcome. Passing the scientific gates is not promised.
Reporting repairs may verify and describe existing evidence; they cannot change
measurements, thresholds, solver rules or the frozen execution allowances.

The original 53-stretch findings, protected ESA groups, four-thread total limit
and prohibition on terminating processes remain in force. New campaigns,
solver experiments, broader aircraft fitting, free-field precision work and
participant expansion require a subsequent reviewed phase.

The [subsequent diagnostic plan](PREDICTION_STOPPING_PLAN.md) is now complete:
32 software checks, four saved points and 646 residual-and-derivative evaluations,
with unchanged acceptance rules. The [small follow-up controls](TIMING_PRECISION_CONTROLS.md)
also finish: 13 software checks, two reporting checks, seven native cases and
zero new fits. The [matched follow-up](saved-point-timing-arithmetic/INTERPRETATION.md)
now explains the timing discrepancy at the saved points but leaves the precision
problem open at that stage. The coordinate-accumulation controls, complete
saved-point check and optimizer qualification now pass. Fresh calibration
subsequently stopped on two cost-stability failures; independent validation
remains blocked without a finite, audited threshold.
The broader backlog remains deferred.

## Dependency-ordered backlog

This table retains the broader roadmap. Items beyond the current phase remain
follow-on work rather than automatic continuation instructions.

Priority shows the order of work. “Software checked” means a calculation passed
known-answer tests; it does not mean the aircraft result has been independently
validated.

| ID | Priority | Status | Work |
|---|---|---|---|
| F01 | Foundation | Complete | [Group related recordings](PROVENANCE_VERIFICATION.md) so overlapping stretches are not counted as independent flights. |
| F02 | Foundation | Complete | [Reserve separate ESA flight groups](PROVENANCE_VERIFICATION.md) for a later independent test. |
| C01 | First | Complete | [Check the basic motion calculations](ilvis0-measurement-contribution/README.md). |
| C02 | First | Software checked | [Test which calibration changes can imitate a model difference](ilvis0-scalar-certificate-controls-20261019/INTERPRETATION.md). |
| C03 | First | Receiver evidence checked; error-law adequacy open | [Include measurement-error assumptions](ilvis0-channel-envelopes-20261019/INTERPRETATION.md) in the accelerometer-only checks. A [training-only scale calculation](ilvis0-shared-training-error/README.md) passes 14 software checks and all [18 recorded assessments](ilvis0-shared-training-error/recorded-assessment/README.md) complete. The [binary inventory](ilvis0-trimble-position-precision/recorded-inventory/README.md) supplies reported precision for 52 files; the [eleven paired comparisons](ilvis0-receiver-overlap/recorded-study/README.md) measure relative agreement. The first six-stream oracle release closed on a software path error; the corrected six-task study completed. Known-calibration forecasts miss by 439–508 m, worse than the original fitted forecasts; a matched full-length noise-free control passes at 0.048 m horizontal RMS. The [sealed same-operator conditioning comparison](noisy-realization-attribution/conditioning-comparison/README.md) finds 717.66 m expected later horizontal scale without earlier receiver updates and 33.77 m after 800 updates. A [ten-variant same-realization replay](noisy-realization-attribution/component-decomposition/README.md) passes, matches the sealed oracle exactly and identifies synthetic gyro bias and white increments as the dominant errors in one preselected case. The [saved receiver-precision check](receiver-precision-holdout/README.md) matches all three pilot recordings but shows that receiver-reported precision alone is much smaller than the observed prediction errors. The [source-bound fixed-law diagnostic](prediction-error-law-qualification/README.md) passes twelve software checks, including a fitted linear mean and an abstention control, and exposes a case where equal training likelihoods imply different future uncertainty. Actual covariance and prediction coverage remain unverified. |
| C04 | First | Recorded scalar check complete; full channel contribution open | [Gyro-free geometry and trajectory controls](ilvis0-measurement-contribution/CHANNEL_CONTROLS.md), derivative and error-budget checks, bounded calibration comparisons, and a [receiver-only window selector](ilvis0-measurement-contribution/SUPPORT_POLICY.md) are complete. The [recorded snapshots](ilvis0-channel-envelopes-20261019/INTERPRETATION.md) and [whole-history scalar check](ilvis0-channel-history-v2-20261019/INTERPRETATION.md) exclude none of the candidates under their stated bounds. That conservative result is useful but does not reconstruct a complete gyro-free flight or isolate the gyro's full contribution. A matched recorded-data fit still needs qualified timing and observational error; fused attitude cannot replace omitted gyro evidence. |
| V01 | First | **24/24 matched controls qualified** | The [revised comparison](ilvis0-near-zero-forecast-controls/README.md) passes every generated case with unchanged physics, bounds and total call limits. It charged 2,976 native calculations. The original 3/24 result remains preserved. This qualifies the tested software procedure, not aircraft adequacy or statistical significance. |
| V02 | First | **Pilot complete; absolute adequacy still open** | The [verified pilot](ilvis0-retrospective-prediction-pilot-v2/INTERPRETATION.md) returns all 72 fits; 49 pass numerical checks. All four matched settings complete on the northern recording, with 0.84–1.13 m later horizontal RMS for specified-field globe versus hundreds of metres for the alternatives. The other two recordings retain numerical or accuracy failures. The [saved-error summary](ilvis0-retrospective-prediction-pilot-v2/ERROR_STRUCTURE.md) finds strong one-second dependence. A [zero-fit receiver-precision comparison](receiver-precision-holdout/README.md) audits 28 qualified primary starts across all three recordings: seven of nine specified-field globe settings pass the earlier accuracy screen, but their median later north/east/height errors are 4.2/4.2/11.0 times receiver-reported sigma. Neither check calibrates observed-aircraft adequacy or significance. |
| L01 | Next | Observed substitution unqualified (21/24) | The [shared covariance component](integrated-noise-covariance/README.md) passes 54 checks and handles 64,080 generated epochs with 59.2 MiB of arrays. The [selective-precision revision](mixed-tangent-hybrid/README.md) passes six twenty-minute kernel checks. The [short paired fit](mixed-tangent-hybrid/paired-qualification/README.md) and [long paired fit](mixed-tangent-hybrid/long-fit-study/README.md) each pass all six generated cases; the largest long-fit forecast difference is 1.63 × 10⁻⁹ m. A [separate timing study](mixed-tangent-hybrid/timed-fit-study/README.md) finds 2.38× median whole-fit CPU speedup. The [verified 24-case ESA audit](esa-observed-hybrid/combined/README.md) finds 21 passing pairs, two nonqualifying matched fits and one 0.016715 m forecast difference above the fixed 0.01 m limit. The revised [three-pair development check](esa-observed-hybrid/three-pair-v2/WALL_CAP.md) sealed all three as wall-cap failures after 349 native calls; no paired comparison completed. The established wide method remains in use. |
| E01 | Next | **Software, inventory and interval preparation complete** | The [72 adapter cases](esa-geographic-rate-controls/README.md), [24 known-correction cases](esa-observation-controls/README.md) and [24 training-only fits](esa-training-forecast-controls/README.md) pass. Two [working receiver-error cases](ESA_ERROR_POLICY.md) pass 76 checks. The [frozen full-motion inventory](esa-development-selection-v2/README.md) admits two runs totaling 393.4 minutes after 154 software checks. The [first twenty-minute interval](esa-development-pilot-preparation/README.md) is prepared and verified. All 48 matched weighted controls pass; actual error coverage remains uncalibrated. |
| E02 | Next | **Pilot complete; prediction-error law open** | The [verified revision](esa-observed-wide-pilot/INTERPRETATION.md) supplies 22 qualified forecasts; three complete settings favor globe plus the specified field, with about 15 m later 3D RMS versus kilometres for the alternatives. Two disc starts reach the runtime ceiling. The [saved precision check](esa-prediction-error-scale/README.md) shows that receiver precision alone cannot describe the later IMU-based forecast error. Error assumptions and broader validation remain open; seven confirmation groups stay protected. |
| G01 | Next | Complete as a descriptive check | [Compare raw gyro trends with geographic predictions](ilvis0-gyro-companion-v2/INTERPRETATION.md) across all 53 stretches. |
| U01 | Next | Development dataset ready | [Assemble the evidence for publication](PAPER_DATASET.md). The 53 stretches fall into 27 conservative groups (11 single, six double, ten triple); every group's recorded numerical preferences are globe plus specified field, but independence and calibrated detection are unproved. Final prediction and uncertainty results are still needed. |
| U02 | Next | **Generated-data calibration and validation complete; aircraft uncertainty open** | The [complete calibration](prediction-calibration-host-20261030/INTERPRETATION.md) verifies all 7,176 forecasts across 299 seed families and supplies a finite error limit. The original validation cohort was interrupted after 3,750 saved fits; a separately frozen [reboot-resumable continuation](prediction-validation-continuation/README.md) completed the other 594. Its combined audit verifies all 4,344 fits across 181 preselected simulated cases, with no threshold exceedance and a 1.64% one-sided 95% failure upper bound. This validates the procedure under its simulated conditions; observed-aircraft error coverage and calibrated Earth-model significance remain open. |
| U03 | Complete | **Combined generated-data validation passed** | The [separate continuation](VALIDATION_CONTINUATION.md) reused 3,750 sealed fits and completed the other 594. An [independently replayed audit](prediction-validation-continuation/README.md) verifies 4,344 passing fits and all 181 simulated cases below the fixed limit. The 95% failure upper bound is 1.64%, below the 5% target. The original validation remains interrupted; aircraft coverage is not established. |
| R01 | Later | Not started | [Estimate the background rotation vector freely](ROTATION_FIELD.md), rather than supplying its rate. |
| R02 | Later | Waiting for R01 | Test whether the measured rate can distinguish sidereal from solar timing. |
| S01 | Later | Deferred | Develop Wuhan-data analysis and the separate [stationary participant experiment](STATIONARY.md). |
| D01 | Supporting | Ongoing | Seek more instrument documentation. This supports the work without stopping analysis under stated assumptions. |

For L01, the [saved-fit failure diagnostic](esa-observed-hybrid/FAILURE_DIAGNOSTIC.md)
measures all three failed ESA pairs without refitting. It narrows the next
method-development check to derivatives evaluated at identical saved points.
The [finite same-point result](esa-observed-hybrid/same-point-result/README.md)
completed all twelve charged native evaluations and independently replayed the
saved arrays. Values and boundary counts agree at all six saved points;
derivative differences reach about 0.0000012 m per normalized parameter unit.
The [revised six-point check](esa-observed-hybrid/same-point-v2/README.md)
passes all six predeclared derivative-improvement gates without refitting.
The faster method remains unqualified for observed substitution, so the
established wide tangent stays in use. The [finite three-pair check](esa-observed-hybrid/three-pair-v2/WALL_CAP.md)
reached its four-hour cap with 0/3 comparisons completed. All three tasks
sealed budget failures after 349 charged native calls; two saved wide fits
passed numerical stopping and one did not. These are hash-checked partial
results. The qualified unfinished-task recovery
route does not apply to these completed budget failures. Any further method
work needs a distinct, prospectively qualified design; it cannot relabel or
retry these results.
C03/V02 real-recording error adequacy is the higher-priority gate.
The new seven-check law-family helper unions matched affine forecast intervals
across supplied error assumptions without choosing a law by training score.
This preserves a known mathematical guarantee only if one supplied Gaussian
law is correct and its calibration box contains truth. It does not calibrate
aircraft prediction coverage or unblock the observed-data adequacy gate.

The [saved ESA error-dependence audit](esa-prediction-error-scale/CORRELATION.md)
now verifies all 22 available forecasts from development recording 187.
Successive forecast errors, about one second apart, remain strongly correlated
after linear detrending;
the 400 later epochs per fit are not independent validation cases. The audit
also finds later errors 84–178 times the fitted earlier residual RMS by axis
for the specified-field globe. Training fit residuals cannot supply a fixed
future error scale on this recording. The
[separate NASA development pilot](ilvis0-retrospective-prediction-pilot-v2/ERROR_STRUCTURE.md)
shows 13–47-fold growth by axis among its nine numerically qualified
specified-field settings. Its saved one-second errors also rise across the
four withheld quarters, especially in height. Neither audit estimates a usable error law or
touches reserved confirmation groups.
The [completed rolling-origin study](prediction-rolling-origin/INTERPRETATION.md)
tests whether error observed before the original withheld period transfers to
an equal-length later forecast. Its 43 source-bound method checks and six
publication checks pass. The separately frozen 48-start NASA development run
returned all tasks: 34 numerically pass, 14 do not, and eight of twelve
clock/processing settings have qualified fits at both cuts. North error ratios
range from 0.44× to 4.09× across these repeated settings; no single future
uncertainty multiplier is calibrated. The historical pilot's source and
results remain preserved.
Four [additional conservative NASA development groups](prediction-group-transfer/README.md)
were fixed using route, IMU type and provenance metadata only. Their
[transfer plan](prediction-group-transfer/OBSERVED_PLAN.md) fixed an
earlier-only empirical error reference and a sixteen-start grid. The
[verified result](prediction-group-transfer/RESULT.md) sealed all 16 fits
under 611 native calls: six passed numerical checks, and three of four
groups have scorable second-cut forecasts. All three meet the descriptive
reference and separate physical screen; one group abstains. This does not
calibrate observed-aircraft coverage or Earth-model significance.
The [saved stopping-probe replay](prediction-group-transfer/STOPPING_DIAGNOSTIC.md)
finds that seven of ten nonpassing fits miss only the original cost-change
check; two miss cost and stationarity, and one stops before the full probe.
The original failures remain unchanged. This directs later numerical-method
work without treating near agreement as convergence.

For C03, an [independent linear known-answer control](PREDICTION_ERROR_LAW_PLAN.md)
checks separate gyro, accelerometer and receiver noise streams. The
[finite identification trial](prediction-known-answer-identification/RESULT.md)
completed 400 generated histories: 166 provisional single-law choices,
234 abstentions and five wrong choices. The true supplied law covered
3,764/4,000 later receiver epochs at the nominal 95% level. This tests a
small fixed-law family; full aircraft prediction and observed error adequacy
remain open.

The [paired aircraft error-law study](prediction-paired-law/RESULT.md) verifies
12 two-minute recordings and 24 matched fits, all passing numerical and
physical prediction screens. The training minimum matches the generating IMU
law in 6/12 comparisons, with no training-score separation above 0.000083.
The largest future scale ratio is 1.0000023; these cadence-matched laws are
nearly equivalent for the receiver forecasts in this two-minute study.
Calibration bounds are active in every comparison;
fixed-parameter 95% marginal coverage is 1,924/2,880 for physical position
and 2,242/2,880 for future receiver reports. These counts do not establish
coverage after fitting. All scientific decisions abstain. Bound-aware
nonlinear uncertainty and independent-seed coverage tests precede any observed
aircraft error-law claim. The [saved ESA timing check](prediction-paired-law/SAMPLING.md)
finds a 1.00000469 accumulated white-noise variance ratio across 239,863
earlier packet intervals, so timing variation in this development interval
does not justify a longer same-cadence law-identification campaign.
The [bound-aware affine control](bounded-calibration-prediction/README.md)
passes nine local tests, including an active-limit Monte Carlo check, an
unidentified-direction case and an independent dense check of its aircraft
forecast adapter. Its 95% marginal guarantee assumes a known Gaussian law
and an affine model. The first [nonlinear generated-aircraft release](bounded-calibration-prediction/NONLINEAR_RESULT.md)
closed 24/24 technical cases with 23/24 combined numerical and accuracy passes.
Its complete interval containment is a development observation, not a
calibrated coverage guarantee. The [saved eight-point probe](bounded-calibration-prediction/TIMING_PROBE_RESULT.md)
rules out packet switching alone as the explanation for the one failed
stopping case, while preserving its terminal technical wrapper and the
original 23/24 result. Coupled calibration/timing behavior remains open.
The separate [two-seed method check](bounded-calibration-prediction/INDEPENDENT_SEEDS_RESULT.md)
passes 48/48 combined numerical and withheld-position screens, but its two
draws per condition do not establish 95% coverage.
A paired-law adapter now saves the union of two bounded marginal
forecast intervals before generated later truth is opened. It preserves
active calibration bounds, binds each interval to its target error operator,
and abstains if either fit is unqualified; eight software checks pass. Fresh
native two-fit controls pass for both generating laws and both calibration
cases on short generated recordings. The
[finite generated-aircraft study](prediction-paired-bound-family/RESULT.md)
now verifies all 24 recordings and 48 matched fits across the original
allowance and a separate four-recording continuation; no
observed-aircraft error law is calibrated by this software check.
Its eight-check saved-result audit independently replayed every withheld score.
Both target intervals contain all later coordinates in 24/24 generated
recordings. The recording, rather than each correlated epoch, is the unit of
the descriptive tally; 95% coverage is not established by this matrix.
The first [whole-period study](prediction-simultaneous-law-family/RESULT.md)
sealed 96/96 package-import failures before any numerical work. It yields no
coverage evidence. A [new independently seeded cohort](prediction-simultaneous-law-family-v2/RESULT.md)
passed a frozen-worker preflight and closed 96/96 tasks across its original
allowance and a qualified continuation of 12 unstarted tasks. Ninety-two
recordings yielded complete paired forecasts; both target intervals contained
every later coordinate in those recordings. Four original tasks stopped at
the eight-hour cap and count as failures. The exact one-sided 95% upper
failure bound is 9.28%, so the declared 5% gate failed. Diagnose the runtime
failures and qualify a new finite check before any observed-flight coverage
claim. No failed or completed task is eligible for an unchanged retry.
A separate five-check affine control also derives a conditional bound for an
entire withheld stretch by allowing for all future coordinates at once. It
remains a mathematical control until nonlinear and observed-aircraft coverage
are qualified in a separate study. Four further checks connect the bound to
both aircraft forecast targets and preserve each target's error-operator
binding through the two-law union. A separate short native generated-aircraft
fit also saves both target intervals before opening later observations. The
two-law union rejects mismatched future time grids; twelve focused checks pass.
This does not establish nonlinear or observed-aircraft coverage.

## Development record

The studies below explain how the current phase was reached. The active tasks
and their gates are in the backlog above. Preserve these completed and failed
results; their old allowances do not authorize rerunning them.

1. Preserve the qualified software controls and completed archival pilot, including
   its numerical and accuracy failures. Broader prediction validation remains open;
   ranges across starts are not calibrated confidence intervals.
2. Preserve the completed ESA comparisons and their failures. The
   [height-gravity revision](esa-observed-height-pilot/README.md) improves the
   matched prediction and completes one adequate three-model setting. Diagnose
   its stopping failures using the [completed fit-free resolution probe](esa-stopping-resolution/README.md).
   The [precision comparison](esa-precision-diagnostic/README.md) completes all
   24 cases: extended integration precision brings all eight field-globe cost
   changes below the existing limit. This diagnoses precision sensitivity at the
   saved points; it does not qualify a revised solver or accept failed fits.
   All [48 long known-motion controls](esa-wide-tangent-controls/README.md) now pass.
   The [matched training study](esa-wide-training-controls/README.md) now
   qualifies all 24 cases, using 268 calls in 113.96 minutes. The
   [observed precision revision](esa-observed-wide-pilot/INTERPRETATION.md) now
   completes three adequate matched comparisons after 56 source-bound checks.
   It preserves all 24 outcomes: 22 numerical passes and two deadline-limited
   starts. The [saved-error check](esa-error-structure/INTERPRETATION.md) now
   verifies all 22 curves without refitting. Errors and their changes remain
   strongly correlated; a receiver-only error assumption is not a complete
   prediction-error law. The [known-noise study](esa-noisy-prediction/README.md)
   completes all 24 fits numerically, but none meets the unchanged physical
   accuracy screen. Later horizontal RMS is 83.6–88.6 m. The
   [verified interpretation](esa-noisy-prediction/INTERPRETATION.md) preserves
   all failures; broader prediction tests remain gated on the revised error model.
   The [training-only rate diagnostic](esa-training-rate-variation/README.md)
   now verifies six-channel variation over 13.33 minutes without fitting. Its
   dependence on sample spacing means that aircraft motion and processing must
   remain distinct from a white sensor-noise assumption. No stress-test setting
   or accuracy limit is changed by this descriptive check.
   The [checked error-budget example](esa-noisy-prediction/ERROR_BUDGET.md)
   also shows why gyro uncertainty accumulates into correlated position errors.
   A revised stochastic prediction-error model needs its own qualification;
   choosing a larger error allowance merely to pass is not a substitute.
   The [shared covariance component](integrated-noise-covariance/README.md)
   now passes 54 software checks, including conditioning across the training
   boundary, stationary changing bias and shared query/endpoint errors. The
   [Native state/input derivatives](native-noise-linearization/README.md) now
   pass 18 source-bound checks across all twelve candidate/processing/gravity
   combinations. Their [complete-history extension](native-noise-linearization/HISTORY_PLAN.md)
   now passes 38 source-bound checks: all twelve longer generated cases preserve
   the nominal positions, and short histories agree with independent nonlinear
   noise perturbations. A separate [receiver extension](integrated-noise-covariance/RECEIVER_PLAN.md)
   passes 15 source-bound checks for offsets, drift, persistent errors and
   earlier-only prediction. Their [combined path](native-noise-linearization/COMBINED_PLAN.md)
   passes twelve native checks with every active calibration column retained.
   The [linear calibration extension](integrated-noise-covariance/CALIBRATION_PLAN.md)
   passes 15 checks and abstains when an unknown calibration direction changes
   the forecast. The separate [ESA rate-point law](integrated-noise-covariance/POINT_PLAN.md)
   passes 15 checks, preserving shared samples between neighboring intervals.
   Its [native adapter](native-noise-linearization/README.md) now passes 65
   checks within a 182-check source-bound suite, retaining both input laws and
   the full 33-state receiver combination. The
   [training-only native adapter](integrated-noise-covariance/training-adapter-qualification/README.md)
   now passes 56 checks. A separate [112-check accounting gate](integrated-noise-covariance/prepaid-native-qualification/README.md)
   permits bounded native blocks without per-packet durable transactions.
   The [sampled-rate error generator](integrated-noise-covariance/rate-point-input-qualification/README.md)
   also passes 54 checks. The [short native protocol](integrated-noise-covariance/short-native-protocol-qualification/README.md)
   now passes 128 software checks. Its two-second cases retain numerical
   nonconvergence and unidentified calibration; they do not qualify longer
   prediction. The [verified two-minute study](structured-noisy-training/README.md)
   now returns all 24 forecasts within the physical screen; 20 pass numerical
   checks. Horizontal RMS is 1.84–2.08 m and height RMS 0.17–0.25 m. Every
   calibration reaches at least one bound, preventing unrestricted uncertainty
   claims. The [saved-data diagnosis](structured-noisy-diagnosis/INTERPRETATION.md)
   now finds strongly coupled gravity/accelerometer columns; the four stopping
   failures miss only cost stability, not their evaluation budgets. The
   [bounded-error adapter](integrated-noise-covariance/bounded-state-qualification/README.md)
   passes 58 checks, its native protocol 69, and the [native connection](integrated-noise-covariance/native-bounded-reference-qualification/README.md)
   all 24 controls. The original 22/24 failure is preserved: an [exact-arithmetic
   diagnosis](integrated-noise-covariance/native-bounded-numerics/README.md) identified
   the dense reference's whitening solve. Nonlinear approximation limits and
   coverage remain before more fits. This shorter study does not supersede the original
   twenty-minute failure. Nonlinear coverage remains open before new aircraft fits.
   Accuracy limits, input selection and calibration bounds remain unchanged.
   The [known-calibration benchmark](noisy-prediction-benchmark/README.md)
   completed all four fixed settings after 27 construction and 14 lifecycle
   checks. With calibration and starting state supplied, the calculated horizontal
   error scale grows from 0.52 m at two minutes to 33.77 m at twenty minutes.
   The longer setting exceeds the unchanged 10 m screen even with this extra
   knowledge. These are assumed-noise calculations, not measured aircraft errors;
   they help explain why longer prediction needs an explicit uncertainty budget.
   The [matched nonlinear check](noise-nonlinearity/README.md) is complete:
   both short settings pass; both longer settings fail the fixed finite test.
   Four of 64 seed/settings controls miss the limit, all in height. The
   [saved diagnosis](noise-nonlinearity/remainder-diagnosis/README.md) locates
   small, closely quadratic effects: largest vertical departures are 7.3 cm
   and 4.4 cm. This supports the covariance calculation as an error-scale
   diagnostic, while preserving its failed strict approximation checks.
   Do not refine those small effects merely to obtain a pass. The next task is
   qualification of the complete fitting-and-uncertainty procedure with unknown
   calibration, separating numerical completion, physical accuracy and coverage.
   Its [saved scoring gate](fitted-prediction-scores/INTERPRETATION.md) is now
   complete: all 24 starts are retained, with 20 numerical passes and ten
   training-selected comparisons available. Their maximum error/noise scores
   are 5.29–6.25; those ratios are not confidence levels. New independent
   calibration/validation draws require their own qualified finite freeze; the
   existing shared seed cannot establish coverage. First [separate draw identity
   from covariance assumptions](prediction-score-qualification/INDEPENDENT_DRAWS.md).
   That interface now passes [30 compatibility checks](prediction-score-qualification/draw-qualification/README.md),
   including identical original-seed outputs against the frozen generator.
   The [fresh-draw pilot](independent-noisy-training-pilot/INTERPRETATION.md) is
   complete: all 48 fits pass numerical and position-error checks. A 17-check
   saved-results audit verifies the new outcomes and reproduces the earlier
   report unchanged. Every selected fit reaches a calibration bound. Their
   error/noise scores are 7.50–11.22 when fitted calibration is treated as known;
   the next step must include its uncertainty rather than enlarge a threshold
   from these two seeds. Neither coverage nor a rare-tail quantile is established.
   The [independent-draw ledger](prediction-score-qualification/calibration-targets-qualification/README.md)
   now passes 30 source-bound checks, including distinct calibration and
   validation targets. It preserves unavailable predictions and rejects
   overlapping draw roles. The [execution design](prediction-score-qualification/EXECUTION_PLAN.md)
   fixes a generated population and separate finite phase allowances, with
   cooperative early stopping if success becomes impossible. Its
   interfaces are now qualified by 62 source-bound checks. The
   [calibration phase](prediction-calibration/README.md) stopped under its
   predeclared futility rule after both starts failed one required setting.
   The [bounded review](prediction-phase-review/README.md) is complete.
   The [four-point diagnostic](prediction-stopping-consistency/INTERPRETATION.md)
   also completes: repeatability is exact, but its derivative comparisons disagree.
   The [small timing controls](timing-precision-controls/INTERPRETATION.md) then
   reproduce packet-boundary slopes and loss of weak coordinate changes.
   Their [matched follow-up](saved-point-timing-arithmetic/INTERPRETATION.md)
   explains the timing discrepancy but leaves gyro-offset comparisons outside
   the fixed scale. No finite threshold or validation result is available.
   The [coordinate controls](coordinate-precision-controls/INTERPRETATION.md)
   pass all six compensated cases. The subsequent [full saved-point check](saved-point-coordinate-precision/INTERPRETATION.md)
   passes all 315 derivative comparisons and all four original stopping probes;
   later solver qualifications and their failures are recorded above.
3. Test broader predictive accuracy before opening the reserved ESA flight groups.
   The [fixed metadata plan](esa-broader-development/README.md) selects the first
   and last twenty minutes of each eligible development run: four ranges, one
   already analyzed and three additional candidates. They share one group and
   require separate preparation and fitting gates. Confirmation groups remain
   untouched until selection, method and decision rules are fixed.
4. Establish confidence at the flight-group level. Then pursue the free rotation
   rate and solar-versus-sidereal studies.

Completed studies remain unchanged. A failed check blocks the work that depends
on it; it does not restart earlier studies or create extra attempts.

Study orchestration and evidence storage use the [shared reproducibility
interface](REPRODUCIBILITY.md). Historical code and evidence retain their original
bytes inside verified archives; storage changes do not alter qualification.

[Plain-language next steps](NEXT_STEPS.md) ·
[Technical requirements and supporting evidence](ANALYSIS_DETAILS.md) ·
[Completed studies](STUDIES.md).
