# Technical requirements and supporting evidence

This reference preserves the detailed checks behind the task IDs.
The [roadmap](ANALYSIS_ROADMAP.md) sets current priorities;
[Next steps](NEXT_STEPS.md) explains them in plain language.

## Evidence behind each task

| ID | Supporting evidence | Required check or limit |
|---|---|---|
| F01 | [Provenance ledger](analysis-provenance/README.md): 53 archive stretches form 27 conservative split groups; physical instrument/installation identity remains unknown. | Eleven metadata controls pass; preserve candidates and conservative grouping separately from verified flight identity. |
| F02 | Nine ESA files form eight groups: recording 187 for development and seven protected confirmation groups. [Policy and ledger](analysis-provenance/README.md). | No protected model fitting or outcome inspection before method freeze. Future workers must enforce the reservation; integrity and receiver-only screening are permitted. |
| C01 | Independent force, receiver-derivative, approximation/averaging and local calibration controls. | [Completed evidence](ilvis0-measurement-contribution/README.md); preserve failures and indistinguishable cases. Do not rerun. |
| C02 | [Feasible scalar calibration](ilvis0-scalar-certificate-controls-20261019/INTERPRETATION.md): 12/12 known-answer identities and 72/72 matched comparisons pass; 147 certificates and 81 actual optimizer starts. | Earlier failed nonlinear study preserved. Handles near-zero scalar ambiguity without claiming unique calibration; observational uncertainty remains C03's gate. |
| C03 | [126 component checks](ilvis0-measurement-contribution/COMBINED_BOUNDS.md) and [two-recording assessment](ilvis0-channel-envelopes-20261019/INTERPRETATION.md): 144/144 scalar envelopes overlap, none unsupported. | Completed freeze; no retries. Physical/error envelopes remain declared assumptions, not calibrated coverage. |
| C04 | [Whole-history necessary constraints](ilvis0-channel-history-v2-20261019/INTERPRETATION.md): all 27,468 scalar cases overlap across 763 packet groups; one zero gain/offset correction survives all 24 history variants. Complete comparisons on both recordings favor globe. | No full gyro-free trajectory or quantitative gyro attribution is established; uncertainty and withheld prediction follow. Preserve conservative error assumptions and all excluded edges. |
| V01 | The [matched training/forecast comparison](ilvis0-near-zero-forecast-controls/README.md) passes all 24 generated cases after 74 focused software checks, retaining all active parameters and unchanged physical assumptions. The original 3/24 result and separate global-bound failures remain preserved. | Qualified on these controls. Aircraft adequacy and calibrated uncertainty are separate requirements; formal interval certification is no longer a prerequisite for exploratory pilots. |
| V02 | The [completed pilot](ilvis0-retrospective-prediction-pilot-v2/INTERPRETATION.md) returns 72 fits, 49 numerically passing, 28 qualified primaries and five complete matched three-model settings. One northern recording completes all four settings with much smaller later errors for specified-field globe. The other two retain numerical or accuracy failures. | Preserve this retrospective result and all failures. Broader predictive adequacy, calibrated uncertainty and independent confirmation remain open. No original allowance is reused. |
| L01 | [Structured covariance](ilvis0-structured-error-controls/INTERPRETATION.md) passes at 64,080 epochs/27 columns with a 24 MiB cache. [Long streaming comparison](ilvis0-streaming-precision/INTERPRETATION.md) passes all six controls: 480,000-packet values and all 27 derivatives match unchanged kernels exactly; traced stream working memory stays below 0.7 MiB. [Native-control sharding](native-sharded-execution/README.md) passes all nineteen execution controls and all 24 native compatibility cases. One-thread native arrays match the four-thread reference bit for bit; complete bound reports match exactly. | Preserve earlier exact-pose failure. No active study changes allocation. Software equivalence does not qualify sampling phase, observational covariance, full-record accuracy or predictive adequacy. |
| E01 | [Version 1 inventory](esa-development-selection/README.md) admits no stretches. The [72 geographic controls](esa-geographic-rate-controls/README.md), [24 known-correction controls](esa-observation-controls/README.md) and [24 training-only fits](esa-training-forecast-controls/README.md) pass. The [working receiver-error adapter](ESA_ERROR_POLICY.md) passes 76 checks, retaining full covariance and candidate-independent weights. | The generated examples contain no random measurement noise, and the receiver cases do not establish calibrated accuracy. The [full-motion inventory](esa-development-selection-v2/README.md) admits two runs totaling 393.4 minutes after 154 software checks. The [first twenty-minute interval](esa-development-pilot-preparation/README.md) is prepared and hash-verified, with an 800/400 training/prediction split. All 48 matched weighted controls pass. |
| E02 | All [48 long motion controls](esa-wide-tangent-controls/README.md), [24 training/forecast cases](esa-wide-training-controls/README.md) and 56 observed adapter/audit checks pass. The [verified observed revision](esa-observed-wide-pilot/INTERPRETATION.md) supplies 22 qualified forecasts and three complete comparisons favoring globe plus the specified field. Its later horizontal/height RMS is 6.8–7.8/13.4–13.7 m; the alternatives have kilometre-scale errors. | Two short-memory, profiled disc starts reach the runtime ceiling. All observations, bounds, starts and accuracy limits remain unchanged, and all earlier results remain preserved. Assess saved error structure and broader prediction accuracy next. Seven confirmation groups remain protected; calibrated confidence is still open. |
| G01 | [All 53 raw-gyro comparisons](ilvis0-gyro-companion-v2/INTERPRETATION.md) follow 48 independent controls. Median absolute rate differences: 0.88°/h specified-field globe, 2.84°/h zero-field globe, 5.87°/h level flat; all 243 fixed scenarios per stretch are preserved. | No fitted gyro correction or fused-attitude subtraction. Unknown aircraft motion/mounting/processing remain; 27 conservative groups are not independent-flight counts. Preserve the prior technical failure and both freezes; no rerun. |
| U01 | [Immutable version 2](PAPER_DATASET.md) retains 53 stretches, 318 latest primaries, 791 history records, 27 conservative groups and gyro baselines; all 326 catalog entries and all history origins are reconciled. Publication and numerical-operation environments remain separate. | Qualified prediction errors, independent confirmation and calibrated uncertainty remain V02/E02/U02 requirements before the final seal. Unknown diagnostic-point ancestry remains explicit; version 1 is preserved. |
| U02 | Calibrate the shape-first decision and subsequent field comparison at the flight-group level. | V02, E02, U01 and separately frozen finite calibration design; include correlated errors, nuisance fitting and minimum over globe candidates. |
| R01 | Freely measured retained background vector and geographic patterns. | C04 and V02; audit geographic/installation rank before fitting. [Field plan](ROTATION_FIELD.md). |
| R02 | Solar/sidereal precision comparison with freely fitted rate. | R01 plus supported clock/gain/bias precision and longer records; no inference from a fixed-rate candidate. |
| S01 | Wuhan independent positions/eligibility and stationary-consumer physical validation. | Separate dataset-specific qualification; no automatic transfer of archive thresholds. |
| D01 | Exact instrument/processing documentation and defensible calibration alternatives. | Supporting work, not a blanket reason to suspend analysis. |

The [calibration-map diagnostic](ilvis0-calibration-map-diagnostic/INTERPRETATION.md)
found that all 36 tested linear extremes were incompatible with their physical
calibrations. That formal-bound method retains the same calibration across training and future
predictions instead of allowing unrelated approximation errors at each epoch.

The [complete three-source rebuild](ilvis0-three-source-complete/INTERPRETATION.md)
passes all 48 regions and all six case covers under the original twofold-width
target. Every case uses all eight fresh regions; no inherited-only fallback
qualifies the result. The rebuild performs no integration. Twelve previously
missing future certificates were separately generated under a qualified serial
recipe without recalculating training bounds. Earlier failed studies retain
their labels.

This qualifies the existing generated 7.2-second width test. It does not qualify
recording-length usefulness, whole-program floating execution or observational
coverage. The [error-assumption guide](PREDICTION_ERROR_ASSUMPTIONS.md) identifies
the separate calibration, approximation, numerical, receiver and inertial-error
requirements. The earlier [formal-bound plan](ilvis0-three-source-complete/NEXT_PLAN.md)
retains its recording-length qualification requirements for that research method.
Current exploratory prediction work follows the separately approved
[revised protocol](PREDICTION_VALIDATION.md).

The separate [ESA position assessment](esa-position-assessment/INTERPRETATION.md)
remains a receiver-motion diagnostic; it does not create an eligible ESA cohort
or validate instantaneous motion between sampled centers.

## Earlier plans and their task IDs

[Prediction error assumptions](PREDICTION_ERROR_ASSUMPTIONS.md) separates the
short generated test's calibration, approximation, arithmetic and observation
allowances from the requirements for real aircraft confidence intervals.

| Existing design or unresolved requirement | Backlog home |
|---|---|
| [Channel-removal requirements](ilvis0-measurement-contribution/CHANNEL_CONTROLS.md), calibration ambiguity and failed nonlinear matrix | C02's mathematical controls and C03/C04's descriptive assessments are complete. Stronger gyro attribution and uncertainty remain V01/V02 work. Preserve every earlier failure. |
| [Error-budget next gate](ilvis0-channel-error-budget-20261019/NEXT_PLAN.md): timing, quantization, averaging, support and joint uncertainty | C03; deterministic count/period and direction-cone bounds are checked, the combined observational model is not. |
| [Shared error-model design](ilvis0-residual-covariance-20261012/ERROR_MODEL_PLAN.md), bounded uncertainty and earlier incomplete prediction studies | V01/V02, L01 and U02; reuse their controls, not completed start allowances. |
| [ESA selection proposal](external-imu-data/ELIGIBILITY_PLAN.md) and rate/axis/lever-arm qualification | E01, with F02 reservation enforced before any development or confirmation fit. |
| Raw gyro geographic-prediction companion, residual trends and shared-recorder comparisons | G01 and V02; no fused-attitude substitution or independent-vote counting. |
| Free vector/latitude/rate/altitude follow-ups and [solar/sidereal precision](ROTATION_FIELD.md) | R01/R02 after contribution and prediction qualification. |
| Wuhan independent GNSS processing, consumer physical controls and exact device documentation | S01/D01; retained as separate secondary/supporting work. |

## Measurement-contribution and prediction rules

The gyro-free magnitude comparison is a necessary constraint, not a complete
motion reconstruction. Agreement does not identify orientation or establish
that a full history fits without gyros. Never insert fused attitude or assumed
aircraft heading to replace omitted observations. Channel costs need not divide
into percentages of gyro and acceleration evidence.

Keep coordinate metric, gravity, calibration, receiver differentiation and
timing dependencies explicit. Select support from receiver motion and
completeness before inspecting model-dependent residuals. Use every nuisance
column in rank checks and retain nonlinear ambiguity.

NASA prediction splits are retrospective development validation: all 53
recordings have informed development. Withhold prediction observations from
calibration, covariance selection and initialization corrections. Distinguish
within-record prediction from calibration transfer across a verified installation.
Report all position components, especially height, rather than rewarding a
better horizontal score with an implausible altitude.

Adequacy thresholds and predictive uncertainty must be specified before evaluation.
A smaller relative error does not establish an adequate model; uncalibrated
criteria remain descriptive. Preserve convergence, physical adequacy, predictive
performance and calibrated detection as separate result fields.

## ESA development and confirmation boundary

Recording 187 is the development recording. All other currently cataloged ESA
flight groups are reserved for confirmation. Inventory, integrity checks and
receiver-only eligibility screening are allowed; model fitting and outcome
inspection are not allowed until the method and confirmation identities are
frozen. Shared files and overlapping flights remain in one group.

The policy is at the flight-group level, not a filename-based claim of independence.
Different dates do not prove a different physical instrument or installation.
If no interval qualifies, publish that result; do not silently relax the policy
or consume confirmation groups for development.

ESA has its own slower-flight eligibility, units, processing assumptions and
calibration bounds. Existing Applanix limits do not automatically transfer.
Long-record infrastructure must avoid dense whole-record covariance/projection
matrices and validate any block/state-space treatment against the dense reference.

## Publication, deferred work and execution safeguards

Preserve the raw gyro plot. Its companion must separate precomputed predictions
from reconstructions using fitted orientation; neither the common sign nor
Group-1 attitude is independent curvature evidence. Report unsupported mounting
or aircraft-motion corrections as unknown.

The paper dataset must preserve source/group/selection versions, failed fits,
all prediction outcomes and exclusions. Calibrate the complete hierarchy,
including selection of the better globe model, field comparison and recording
dependence, before attaching significance or promoting production thresholds.

Further NASA recovery, broad horizontal timing searches, large Z-axis grids
and passenger-flight geometry optimization are retired or deferred. Precise
device identification remains supporting work. Free-field precision, Wuhan
expansion and stationary-consumer expansion follow the higher-priority gates.

Each new numerical study needs a separate source/input/environment freeze,
finite starts/evaluations, at most four total numerical threads and no adaptive
retries. Completed studies never restart or donate unused allowance. Failed
qualification blocks dependent observed fits. No automatic corpus-wide campaign
or production promotion follows from this roadmap.

[Public next steps](NEXT_STEPS.md) · [Diagnostic requirements](ILVIS0_DIAGNOSTIC_PLAN.md).
