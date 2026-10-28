# What comes next

**The main comparison is complete: all 53 selected stretches fit globe geometry
better than the tested flat-disc model.** All also favor the model with a
specified background rotation signal over zero. This does not yet give a tested
statistical confidence level or identify the signal's cause.

An **IMU (inertial measurement unit)** records turning with gyroscopes and
specific force with accelerometers. The gyroscope records are central to this
study; receiver positions help constrain the reconstructed flight.

[Current findings](CURRENT_STATUS.md) ·
[All 53 stretches](ilvis0-current-findings-20261015/STRETCHES.md) ·
[Detailed CSV](ilvis0-current-findings-20261015/stretch-analytics.csv).

<a id="then-strengthen-the-interpretation"></a>

## Now: predict measurements left out of the fit

**Compensated coordinates pass the [small known-answer controls](coordinate-precision-controls/INTERPRETATION.md).**
All six coordinate cases now meet the precision tolerance, compared with three
for the original arithmetic and four for the longitude-only change. This follows
the [four-point diagnostic](saved-point-timing-arithmetic/INTERPRETATION.md),
which resolved the timing discrepancy but left gyro-bias precision unresolved.

**Complete:** the [full saved-point check](saved-point-coordinate-precision/INTERPRETATION.md)
passes all 315 derivative comparisons and all four original stopping probes,
including the two previously failed examples. It finishes in 27.2 minutes after
99 software checks. No fit is run or relabeled.

**Complete:** [qualification during optimization](compensated-optimizer-qualification/INTERPRETATION.md)
passes all 48 generated development fits and all 24 paired-start comparisons.
All four original input/error bindings reproduce exactly. The run finishes in
30.3 minutes after 93 software checks, with unchanged numerical and physical limits.

**Stopped:** the [fresh calibration outcome](prediction-calibration-compensated/INTERPRETATION.md)
records 909 returned starts in 9.58 hours: 904 passed, two failed the numerical
cost-stability check and three stopped cooperatively. All 906 completed forecasts
met the fixed position-error limits. The run supplied no uncertainty threshold.

The [timing-only saved review](prediction-clock-boundary-review/README.md)
places every query near an internal integration boundary: about 304 nanoseconds
away for one start and 3.8 nanoseconds for the other. Exact clock hashes match.
This suggests checking both timing branches; proximity does not prove the cause.

The [saved linear-correction review](prediction-linear-timing-review/README.md)
now reproduces all four saved probes. Both failed corrections cross all 119
query boundaries; neither successful control crosses one. This narrows the
diagnostic without proving a derivative error or qualifying a failed fit.

The [four analytical controls](timing-kink-controls/README.md) now demonstrate
that the unchanged smooth stability check can reject exact minima at a slope
change, even with correct derivatives. The smooth controls behave as expected.
This establishes a numerical limitation, not the cause of the saved failures.

**Complete:** the [four-point physical calculation](saved-timing-boundary/INTERPRETATION.md)
replays all saved inputs, residuals and 27-column Jacobians exactly. All 18
within-interval timing derivative checks agree. The failed combined corrections
nearly cancel large timing and calibration effects, while the timing movement
accounts for most of the error in the local prediction. The run used 78
residual/Jacobian evaluations in 6.7 minutes; no model was refitted.

**Complete:** [bounded steps within timing intervals](TIMING_CELL_STEP_PLAN.md)
pass independent known-answer qualification. The
[saved-matrix review](saved-timing-cell-proposals/INTERPRETATION.md) now passes
all 18 linear solves after 26 software checks. Both sides and every spacing
propose the same boundary for each failed case. Their remaining predicted cost
improvements are below the original stability limit; actual physical costs
have not yet been evaluated.

**Complete:** [all 18 proposals pass their physical checks](saved-timing-cell-native/INTERPRETATION.md).
The run uses 26 evaluations in 2.6 minutes after 103 software checks. Every
proposal passes the original cost, stationarity and actual position-change
screens; the largest position change is about 1.5 micrometres.

**Next gate:** qualify a complete optimizer using the interval-constrained
component, with independent known-optimum and non-optimum controls and repeated
starts. Keep all nuisance directions and the original limits.
**Complete:** [analytical qualification](timing-stopping-qualification/INTERPRETATION.md)
passes all 32 fits and eight direct controls. Different starts agree for all
eight objective families. The run takes 26 seconds after 161 software checks.
**Finished, not qualified:** the [four native regressions](timing-optimizer-regression/INTERPRETATION.md)
replay all original inputs, but all four fail final cost stability. Their
position forecasts meet the declared screens. Distant timing-cell midpoints
are the next specific issue to test; a known curved objective reproduces a
false failure with midpoint anchors and passes with local anchors.
**Complete:** the [local timing checks](timing-local-qualification/INTERPRETATION.md)
pass all 36 known-answer fits, eight direct controls and nine starting-point
comparisons in 27.5 seconds after 175 software checks. Simply choosing the
nearest point failed sharp-corner tests and was rejected before this study.
This version samples both sides near the fitted timing value; every acceptance
threshold stays unchanged. No aircraft observations are used.
**Complete:** the [new four-case simulator trial](timing-local-native-regression/INTERPRETATION.md)
passes all four fits, both paired-start checks and all original input replays
in 10.7 minutes after 189 software checks. It retains the original inputs,
starting points and acceptance limits. The earlier failed trial stays preserved.
**Complete:** the [48-case matrix](timing-local-matrix/INTERPRETATION.md)
passes all fits, all 24 paired-start checks and four original input replays
in 65.7 minutes after 203 software checks. It covers both input formats, all
three generating candidates and both processing settings, with the original
starts, bounds and limits. This completes the declared optimizer qualification.
**Stopped:** the [local-timing calibration](prediction-calibration-timing/INTERPRETATION.md)
returned 348 of 7,176 planned starts in 6.82 hours. Of these, 344 passed,
two failed timing-cell stability and two stopped cooperatively. All 346
completed forecasts met the position-error limits. The independently checked
outcome supplies no calibration threshold, so validation was not launched.
**Diagnosed:** the [four saved-baseline checks](timing-linear-baseline-diagnosis/README.md)
reproduce worse linear proposals in both failed cases; the matched earlier
controls do not worsen. Four linear solves were charged, with no native
calculations or refits. A result-schema error rejected the task envelopes;
their saved calculations and accounting were verified without a rerun.
**Correction checked:** [feasible initialization](timing-linear-anchor-check/INTERPRETATION.md)
passes all 24 independent convex controls and all four matched saved-matrix
calculations, after 56 source-bound checks. Another 90 related software tests
pass. The earlier method fails ten of the same 24 controls.
**Complete optimizer checked:** the [new analytical qualification](timing-feasible-optimizer-qualification/INTERPRETATION.md)
passes all 36 known-answer fits, eight direct probes and nine starting-point
groups in 27.8 seconds after 148 software checks.
**Native regression checked:** [all six fits pass](timing-feasible-native-regression/INTERPRETATION.md),
along with three start pairs and six exact original-input replays. The run
finishes in 10.6 minutes on four threads. The latest formerly failing case
passes at the same fitted cost and prediction errors under the original checks.
**Finished:** the [matrix audit](timing-feasible-matrix/INTERPRETATION.md)
accepts all 44 completed fits and 22 complete start pairs in 51.0 minutes.
Four starts were interrupted by a runtime reset and remain charged; none was
retried. The interrupted study cannot establish full 48-case qualification.
A [separate four-case follow-up](timing-matrix-completion/INTERPRETATION.md)
passes all four fits, both start pairs and the remaining input replay in
4.6 minutes after 364 software checks. The
[combined coverage audit](timing-matrix-combined/README.md) now qualifies all
48 computational cases, all 24 pairs and all four original replays, with
identical shared sources and environment. Sixteen additional assembler checks
pass; the interrupted study's failure labels remain unchanged.
**Running:** the [fresh calibration release](FEASIBLE_PREDICTION_STATUS.md)
uses four threads after 98 software checks and a 253-source freeze. Calibration
covers 299 new simulated families; validation on 181 separate families will
follow only after a complete, finite, audited handoff. Expected total runtime
is about nine days. A calibration threshold is still
unavailable. Keep all directions, bounds and limits; closed campaigns do not restart.
The existing failures are not relabeled; another solver trial or campaign needs
its own finite, source-bound phase.
No additional campaign starts automatically. Independent validation remains
blocked; all closed calibration campaigns and their unused allowances stay closed.
Protected aircraft groups remain untouched. These generated-data tests do not
establish actual flight-level confidence.

The [preceding calibration phase](PREDICTION_PHASE_RESULTS.md)
stopped after both starts failed one required setting. It produced
no usable uncertainty threshold, so validation was not launched. The single
saved-results review identifies a numerical cost-stability failure despite
small position changes. Further campaigns and method changes require a new
reviewed phase; the development backlog below remains deferred.

The [earlier bounded diagnostic](PREDICTION_STOPPING_PLAN.md) passed its 32
software checks and returned all four native tasks in 35.2 minutes. None passes
every derivative comparison, including the successful controls. The
[follow-up controls](TIMING_PRECISION_CONTROLS.md) add 13 software checks,
two reporting checks and 49 native evaluations, with zero new model fits.
The subsequent matched comparison passes 42 software checks and returns all
four tasks in 13.1 minutes using 208 residual-and-derivative evaluations.

Fit the earlier part of a recording, then reconstruct the later track from its
IMU readings. Keep later GPS positions out of calibration and use them only to
measure the errors. Check height as well as the horizontal track.

The [revised protocol](PREDICTION_VALIDATION.md) has reached these checkpoints:

1. **Complete:** the [matched software comparison](ilvis0-near-zero-forecast-controls/README.md)
   passes all 24 known-answer cases.
2. **Complete:** the [three-recording pilot](ilvis0-retrospective-prediction-pilot-v2/INTERPRETATION.md)
   returns every planned fit. One recording completes the full comparison;
   the other two retain numerical or accuracy failures.
3. **Software checked:** the [ESA rate adapter](esa-geographic-rate-controls/README.md)
   passes all 72 generated maneuvering cases. Linear point samples stay below
   10 cm maximum position error; holding samples constant produces much larger
   errors. The instrument's actual sampling behavior remains to be established.
4. **Software checked:** all 24 [antenna and calibration cases](esa-observation-controls/README.md)
   pass when the corrections are supplied. Maximum position error stays below 10 cm.
5. **Software checked:** all 24 [training-only fits](esa-training-forecast-controls/README.md)
   pass numerical and later-position checks. The examples have synthetic
   calibration errors and no random measurement noise.
6. **Software checked:** two [working receiver-error cases](ESA_ERROR_POLICY.md)
   retain full covariance and test short-lived or persistent errors. Their
   numerical checks do not establish calibrated accuracy.
7. **Complete:** the [revised ESA inventory](esa-development-selection-v2/README.md)
   admits two full-motion runs totaling 393.4 minutes. They contain turns and climbs;
   they are not certified level-flight intervals.
8. **Complete:** the [first ESA interval](esa-development-pilot-preparation/README.md)
   is prepared: 360,029 raw IMU samples, with 800 earlier receiver positions for
   training and 400 later positions for prediction checks. Full source hashes match.
9. **Complete:** all 48 [weighted fitting controls](esa-weighted-training-controls/README.md)
   pass and their saved evidence is verified. These are noiseless software examples.
10. **Complete, with accuracy failures:** the [ESA pilot](esa-development-pilot/README.md)
    returned all 24 fits; 15 pass numerical checks. One of four three-model
    comparisons completes and has lower error for globe geometry, but its
    preferred forecast misses the accuracy limits. This is not a successful
    independent replication. A [completed saved-data diagnosis](esa-development-diagnosis/README.md)
    preserves the forecasts, finds calibration at bounds and identifies gravity
    treatment as a hypothesis to [test independently](esa-gravity-controls/PLAN.md)
    before more fitting.
    Reserved confirmation flights stay protected.
11. **Complete:** all 48 [gravity controls](esa-gravity-controls/README.md) pass.
    The largest height-dependent-gravity error is about 11 cm at 300 Hz and 2.7 cm
    at 600 Hz. These twenty-minute examples supply true calibration and initial state.
12. **Complete:** all 24 [long training/forecast controls](esa-height-training-controls/README.md)
    pass after learning calibration from earlier generated positions. Later errors
    stay below 0.02 mm in these noiseless examples; that is software accuracy,
    not measured instrument precision.
13. **Complete:** the [observed gravity revision](esa-observed-height-pilot/README.md)
    returns all 24 forecasts; eight fits pass numerical checks. One complete
    three-model setting favors globe and meets the unchanged accuracy limits:
    6.80 m horizontal and 13.71 m height RMS for the specified-field model.
    The alternatives miss by kilometres. Other settings remain unresolved.
14. **Complete:** all 24 [fixed-point stopping diagnostics](esa-stopping-resolution/README.md)
    reproduce the saved costs and numerical outcomes. Seven field-globe fits still
    fail cost stability, although their local position changes stay below
    4 micrometres. Exact repeats rule out random run-to-run differences.
    They do not establish why tiny calibration changes upset the cost check.
15. **Complete:** the [precision comparison](esa-precision-diagnostic/README.md)
    verifies all 24 cases after 31 software checks. It uses 96 value calculations
    in 67 seconds. Extended precision brings all eight field-globe cost changes
    below the unchanged limit; changing longitude wrapping alone is insufficient.
    Every original binary64 residual is reproduced exactly.
16. **Complete:** all 48 [long known-motion controls](esa-wide-tangent-controls/README.md)
    pass in 38.87 minutes. The wider tangent retains every column and agrees with
    the unchanged value calculation within 0.0000383 m in the reported comparison.
17. **Qualified:** all 24 [matched training/forecast controls](esa-wide-training-controls/README.md)
    pass after 268 native calls in 113.96 minutes. Their saved-results audit
    verifies every case and charge. These noiseless software controls retain
    the original bounds, stopping checks and prediction limits.
18. **Verified:** the [observed-data precision revision](esa-observed-wide-pilot/INTERPRETATION.md)
    supplies 22 qualified forecasts and three complete comparisons. Each favors
    globe plus the specified field and passes physical accuracy, with about
    15 m later 3D RMS versus kilometres for the alternatives. Two disc starts
    reach the eight-hour ceiling; their setting remains incomplete.
19. **Complete:** the [saved-error check](esa-error-structure/INTERPRETATION.md)
    preserves all 22 forecasts. Nearby errors remain strongly correlated,
    including their first differences. No fits or predictions are repeated.
    The errors cannot be counted as independent tests.
20. **Accuracy failed:** all [24 noisy-data fits](esa-noisy-prediction/INTERPRETATION.md)
    converge numerically, but later horizontal RMS is 83.6–88.6 m against the
    unchanged 10 m target. Each candidate predicts its own generating truth;
    these are not Earth-model votes. Error propagation and calibration
    uncertainty need further work before broader observed fitting.
21. **Not qualified:** the [faster-arithmetic benchmark](mixed-tangent-long-controls/README.md)
    preserves predicted positions exactly on all six long cases, but fails the
    derivative tolerance. It runs 4.7–5.6× faster; the existing method stays in use.
22. **Complete:** the [training-rate diagnostic](esa-training-rate-variation/README.md)
    examines 13.33 minutes of saved measurements without fitting. Short-term
    variation depends strongly on sample spacing. Motion and processing must
    be separated from sensor noise before deriving a physical error model.

The [shared accumulated-error calculation](integrated-noise-covariance/README.md)
now passes 54 software checks, including future uncertainty conditioned only on
earlier errors, slowly changing bias and shared query/endpoint noise. It handles long generated
records with linear memory. The [native single-step derivative bridge](native-noise-linearization/README.md)
passes 18 source-bound checks; its complete-history extension now passes
another 38. A separate receiver extension passes 15 checks for offsets, drift
and persistent errors; their combined path passes twelve native checks.
Fifteen further checks include calibration uncertainty in a linear prediction.
ESA logs rates, and neighboring converted intervals share a sample. That law
passes 15 checks. Its [native adapter](native-noise-linearization/README.md)
now passes 65 checks within a 182-check qualification, retaining all error
states and the original incremental-data path. The
[training-only fitting adapter](integrated-noise-covariance/training-adapter-qualification/README.md)
now passes 56 checks, preserving all calibration columns and earlier-only error
corrections. Efficient work accounting passes 112 checks, and sampled-rate error
generation passes 54. Next: qualify [nonlinear fitting and parameters at their
bounds](integrated-noise-covariance/NONLINEAR_PLAN.md) with declared measurement
noise. The [short native protocol](integrated-noise-covariance/short-native-protocol-qualification/README.md)
passes 128 software checks, while preserving the two-second cases' numerical
failures and unidentified calibration. The [verified two-minute study](structured-noisy-training/README.md)
returns 24 accurate raw and conditional forecasts, with 20 numerical passes.
All calibrations reach a bound. The [completed saved-data check](structured-noisy-diagnosis/INTERPRETATION.md)
finds a strong trade-off between gravity and accelerometer calibration. The
four numerical failures miss cost stability rather than exhausting their budgets.
The [bounded native interface](integrated-noise-covariance/native-bounded-reference-qualification/README.md)
now passes all 24 controls, retaining calibration limits and unknown directions.
Exact arithmetic identified and corrected an unstable solve in the dense test
reference; the original failed trial remains recorded. Next: justify nonlinear
approximation allowances and test coverage before claiming useful uncertainty.
The [known-calibration noise benchmark](noisy-prediction-benchmark/README.md)
has completed all four settings. With known calibration and starting state,
the calculated horizontal error scale is 0.52 m for two minutes and 33.77 m
for twenty minutes; height scales are 0.20 m and 1.95 m. Both declared input-error
formats agree closely. These are expected noise scales, not measured flight
errors. The longer horizontal scale exceeds the unchanged 10 m screen, making
the uncertainty budget essential before another long fitting study.
The [completed nonlinear check](noise-nonlinearity/README.md) passes both short
settings but retains failures in both longer settings. Four of 64 matched
controls miss the fixed limit, all in height. The [saved diagnosis](noise-nonlinearity/remainder-diagnosis/README.md)
finds small quadratic effects, with largest vertical departures of 7.3 cm and
4.4 cm. These do not explain metre-scale fitting errors by themselves. Next:
qualify uncertainty when calibration must be estimated, rather than supplied.
The [saved-score step](fitted-prediction-scores/INTERPRETATION.md) is complete:
all 24 starts are retained, with 20 numerical passes and ten available primaries.
Their maximum error/noise ratios are 5.29–6.25, not confidence levels. Next:
use independent noise realizations to test the complete fitting procedure,
keeping the noise law, calibration bounds and accuracy screens fixed.
The [draw interface](prediction-score-qualification/draw-qualification/README.md)
passes 30 checks against the earlier frozen generator. The [fresh-draw pilot](independent-noisy-training-pilot/INTERPRETATION.md)
is complete: all 48 starts pass numerical and position-error checks. The 24
training-selected forecasts miss their targets by 2.49–3.78 m horizontally.
Every selected calibration reaches a bound. Error/noise scores of 7.50–11.22
exclude calibration uncertainty; they are not confidence levels. Next include
that uncertainty, preserving the same calibration limits and unknown directions.
The [calibration bookkeeping](prediction-score-qualification/calibration-targets-qualification/README.md)
passes 30 checks. It counts independent seed families, preserves unavailable fits
and separates calibration from validation. The [sample-size estimates](prediction-score-qualification/CAMPAIGN_SIZING.md)
show why two pilot seeds cannot establish coverage; the generating calibration
population and finite campaign allowance have a separate
[execution design](prediction-score-qualification/EXECUTION_PLAN.md). Its
[execution interfaces](prediction-score-qualification/execution-qualification/README.md)
pass 62 checks. [Calibration stopped](prediction-calibration/README.md) after
1,686 returned starts because both starts failed one required setting.
The [phase report](PREDICTION_PHASE_RESULTS.md) preserves the failure and the
bounded diagnosis. No validation or additional aircraft fitting was released.
The shorter duration means this does
not replace the earlier twenty-minute failure; uncertainty remains unqualified.

The [broader development plan](esa-broader-development/README.md) is fixed from
saved metadata: first and last twenty-minute ranges in each eligible run. One
range is already analyzed; three are additional candidates. These share one
development group and are not independent replications. No new measurements
have been extracted or fitted; the preceding checks and separate preparation
gates still apply.

The [stopping-check explanation](NUMERICAL_STOPPING.md) distinguishes numerical
failures from inaccurate predictions. A shared saved-results diagnostic now
identifies which check failed, while preserving the original labels.
The [completed four-point check](prediction-stopping-consistency/INTERPRETATION.md)
finds exact repeatability alongside timing and finite-difference precision
discrepancies. The subsequent small controls and complete saved-point checks
now pass. The optimizer qualification above tests the correction during fitting;
another calibration run remains a separate gate.

On the fully compared northern recording, later horizontal RMS is 0.84–1.13 m
for specified-field globe, about 496 m for zero-field globe and 793 m for disc.
Both clocks and both processing assumptions retain that difference. These four
settings reuse one recording; they are not four independent replications.
Broader prediction validation and calibrated confidence remain open.

Formal bounds covering every allowed calibration are a separate research track.
They no longer block exploratory prediction comparisons. The current bounded
calculation finished without qualifying; its failures are preserved, with no
new expansion of its limits.

This change does not turn sensitivity ranges into confidence intervals or model
preferences into detections. Actual measurement-error assumptions and calibrated
statistical confidence still need testing. The 53-stretch findings are unchanged,
and reserved ESA confirmation groups remain protected.

[Prediction protocol](PREDICTION_VALIDATION.md) ·
[Error assumptions](PREDICTION_ERROR_ASSUMPTIONS.md) · [Study history](STUDIES.md).

## Then: four larger tests

| Order | Question | What is needed |
|---|---|---|
| 1 | **Can the models predict unused measurements?** | Fit earlier observations and predict later ones. Height must agree too; a better horizontal fit alone is insufficient. |
| 2 | **Does the result repeat in a different archive?** | Three ESA development settings now complete adequate three-model prediction comparisons on one recording. Assess the error assumptions and broader accuracy before evaluating the reserved confirmation flights. |
| 3 | **How much independent evidence is there?** | Group overlapping recordings and related flights. Establish confidence without counting every stretch as an independent experiment. |
| 4 | **What rotation field does the data measure?** | Fit its size and direction freely. Only then assess whether the precision can distinguish solar from sidereal timing. |

## What is already done

- All 53 main comparisons passed their numerical stopping checks.
- The [raw-gyro companion](ilvis0-gyro-companion-v2/INTERPRETATION.md) compares
  observed trends with geographic predictions across all 53 stretches.
- Initial checks without gyroscopes leave all candidate models possible.
  Those checks are not complete reconstructions of flights without gyros.
- Long-record processing has passed software tests. Separate ESA flight groups
  are reserved for confirmation.

The earlier airborne archive has already informed development. Tests on it can
check prediction performance, but they cannot become an untouched independent
confirmation. That is the purpose of the reserved ESA flights.

[Roadmap and task status](ANALYSIS_ROADMAP.md) ·
[Method](METHODOLOGY.md) · [Completed studies](STUDIES.md) · [Reproducibility](REPRODUCIBILITY.md) ·
[Rotation-field proposal](ROTATION_FIELD.md).
