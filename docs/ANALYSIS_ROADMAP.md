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

Global interval certification is now a separate research track. Its earlier
bounds and counterexamples remain published, with unchanged failure labels and
width targets. The [completed training-bound study](ilvis0-dense-physical-bounds/INTERPRETATION.md)
preserved 348 reports, but none of its six cases qualified. No further bound
expansion precedes the revised prediction sequence.

[Revised method and safeguards](PREDICTION_VALIDATION.md) ·
[Error assumptions](PREDICTION_ERROR_ASSUMPTIONS.md) · [Study history](STUDIES.md).

## Current phase and finish line

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
The [fresh calibration release](FEASIBLE_PREDICTION_STATUS.md) is now running
on four threads after 98 software checks and a 253-source freeze. Calibration
uses 299 new families; independent validation on 181 separate families is
authorized only after a complete finite audited handoff. Expected combined
runtime is about nine days. All earlier allowances stay closed.
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
| F01 | Foundation | Complete | [Group related recordings](analysis-provenance/README.md) so overlapping stretches are not counted as independent flights. |
| F02 | Foundation | Complete | [Reserve separate ESA flight groups](analysis-provenance/README.md) for a later independent test. |
| C01 | First | Complete | [Check the basic motion calculations](ilvis0-measurement-contribution/README.md). |
| C02 | First | Software checked | [Test which calibration changes can imitate a model difference](ilvis0-scalar-certificate-controls-20261019/INTERPRETATION.md). |
| C03 | First | Initial check complete | [Include measurement-error assumptions](ilvis0-channel-envelopes-20261019/INTERPRETATION.md) in the accelerometer-only checks. |
| C04 | First | Initial check complete | [Compare checks without gyroscopes](ilvis0-channel-history-v2-20261019/INTERPRETATION.md). These leave all models possible; they do not reconstruct a complete flight. |
| V01 | First | **24/24 matched controls qualified** | The [revised comparison](ilvis0-near-zero-forecast-controls/README.md) passes every generated case with unchanged physics, bounds and total call limits. It charged 2,976 native calculations. The original 3/24 result remains preserved. This qualifies the tested software procedure, not aircraft adequacy or statistical significance. |
| V02 | First | **Pilot complete: one recording passes the full prediction comparison** | The [verified pilot](ilvis0-retrospective-prediction-pilot-v2/INTERPRETATION.md) returns all 72 fits; 49 pass numerical checks. All four matched settings complete on the northern recording, with 0.84–1.13 m later horizontal RMS for specified-field globe versus hundreds of metres for the alternatives. The other two recordings retain numerical or accuracy failures. |
| L01 | Next | Accumulated-error covariance and conditioning software checked | The [new shared component](integrated-noise-covariance/README.md) passes 54 checks, including earlier-only prediction, slowly changing bias and shared query/endpoint noise. Its eight-state storage case handles 64,080 generated epochs with 59.2 MiB of arrays. The [faster arithmetic prototype](mixed-tangent-long-controls/README.md) remains unqualified because its derivatives miss the fixed tolerance. |
| E01 | Next | **Software, inventory and interval preparation complete** | The [72 adapter cases](esa-geographic-rate-controls/README.md), [24 known-correction cases](esa-observation-controls/README.md) and [24 training-only fits](esa-training-forecast-controls/README.md) pass. Two [working receiver-error cases](ESA_ERROR_POLICY.md) pass 76 checks. The [frozen full-motion inventory](esa-development-selection-v2/README.md) admits two runs totaling 393.4 minutes after 154 software checks. The [first twenty-minute interval](esa-development-pilot-preparation/README.md) is prepared and verified. All 48 matched weighted controls pass; actual error coverage remains uncalibrated. |
| E02 | Next | **Pilot complete: three adequate matched comparisons** | The [verified revision](esa-observed-wide-pilot/INTERPRETATION.md) supplies 22 qualified forecasts; three complete settings favor globe plus the specified field, with about 15 m later 3D RMS versus kilometres for the alternatives. Two disc starts reach the runtime ceiling. Error assumptions and broader validation remain open; seven confirmation groups stay protected. |
| G01 | Next | Complete as a descriptive check | [Compare raw gyro trends with geographic predictions](ilvis0-gyro-companion-v2/INTERPRETATION.md) across all 53 stretches. |
| U01 | Next | Development dataset ready | [Assemble the evidence for publication](PAPER_DATASET.md). Final prediction and uncertainty results are still needed. |
| U02 | Active | **Fresh calibration running** | The [new release](FEASIBLE_PREDICTION_STATUS.md) runs on four threads after 98 software checks and a 253-source freeze. Independent validation follows only after complete finite audited calibration. The [48-case gate](timing-matrix-combined/README.md) qualifies; no calibration threshold is available yet. |
| R01 | Later | Not started | [Estimate the background rotation vector freely](ROTATION_FIELD.md), rather than supplying its rate. |
| R02 | Later | Waiting for R01 | Test whether the measured rate can distinguish sidereal from solar timing. |
| S01 | Later | Deferred | Develop Wuhan-data analysis and the separate [stationary participant experiment](STATIONARY.md). |
| D01 | Supporting | Ongoing | Seek more instrument documentation. This supports the work without stopping analysis under stated assumptions. |

## What happens after the current diagnostic

The development backlog below is deferred for review. It does not authorize
another study after the completed calibration phase.

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
   pass all six compensated cases. Complete the full saved-point derivative
   and stopping check before another solver trial.
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
