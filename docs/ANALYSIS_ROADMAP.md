# Analysis roadmap

## Starting point

<!-- current-status:start -->
**53 globe preferences, 0 flat preferences, 0 unresolved** among 53 preselected stretches.
See the [verified current status](CURRENT_STATUS.md) for coverage, background-field comparisons and the supporting result records. All selected comparisons have passed their required numerical checks.
<!-- current-status:end -->

The complete full-position comparison covers 424.3 minutes. All 53 stretches
also prefer the specified nonzero background field over zero under both tested
processing assumptions. These are numerical preferences, not a significance
level or 53 independent flights.

An **IMU (inertial measurement unit)** records turning and specific force.
Gyroscopes supply the turning observations; accelerometers and primary-receiver
positions constrain reconstructed motion. Group-1 fused navigation is context
and decoder-check material, not independent fitted evidence.

This is the authoritative backlog. Detailed study plans define their own frozen
allowances; they do not create competing execution queues. Status changes below
must link to evidence. Runtime state belongs in worker metadata.

## Dependency-ordered backlog

| ID | Priority / status | Work and output | Depends on / completion gate |
|---|---|---|---|
| F01 | Foundation — metadata ledger complete | [Provenance ledger](analysis-provenance/README.md): 53 archive stretches form 27 conservative split groups; physical instrument/installation identity remains unknown. | Eleven metadata controls pass; preserve candidates and conservative grouping separately from verified flight identity. |
| F02 | Foundation — reservation recorded | Nine ESA files form eight groups: recording 187 for development and seven protected confirmation groups. [Policy and ledger](analysis-provenance/README.md). | No protected model fitting or outcome inspection before method freeze. Future workers must enforce the reservation; integrity and receiver-only screening are permitted. |
| C01 | P0 — complete | Independent force, receiver-derivative, approximation/averaging and local calibration controls. | [Completed evidence](ilvis0-measurement-contribution/README.md); preserve failures and indistinguishable cases. Do not rerun. |
| C02 | P0 — mathematical controls qualified | [Feasible scalar calibration](ilvis0-scalar-certificate-controls-20261019/INTERPRETATION.md): 12/12 known-answer identities and 72/72 matched comparisons pass; 147 certificates and 81 actual optimizer starts. | Earlier failed nonlinear study preserved. Handles near-zero scalar ambiguity without claiming unique calibration; observational uncertainty remains C03's gate. |
| C03 | P0 — snapshot assessment complete | [126 component checks](ilvis0-measurement-contribution/COMBINED_BOUNDS.md) and [two-recording assessment](ilvis0-channel-envelopes-20261019/INTERPRETATION.md): 144/144 scalar envelopes overlap, none unsupported. | Completed freeze; no retries. Physical/error envelopes remain declared assumptions, not calibrated coverage. |
| C04 | P0 — descriptive comparison complete | [Whole-history necessary constraints](ilvis0-channel-history-v2-20261019/INTERPRETATION.md): all 27,468 scalar cases overlap across 763 packet groups; one zero gain/offset correction survives all 24 history variants. Complete comparisons on both recordings favor globe. | No full gyro-free trajectory or quantitative gyro attribution is established; uncertainty and withheld prediction follow. Preserve conservative error assumptions and all excluded edges. |
| V01 | P0 — short controls and shared-scale software pass; recording-scale usefulness fails | [Prediction coverage](ilvis0-bounded-prediction-controls/README.md), [interface](ilvis0-bounded-prediction-controls/NATIVE_INTERFACE.md), [increment bounds](ilvis0-increment-remainders/INTERPRETATION.md), [local](ilvis0-local-step-bounds/INTERPRETATION.md), [geographic](ilvis0-geographic-step-bounds/INTERPRETATION.md) and [54 short-history controls](ilvis0-history-bounds/INTERPRETATION.md) pass. [Shared-reference scale](ilvis0-shared-reference-scale/INTERPRETATION.md) passes all eight families/8,192 assessments. The [recording-scale study](ilvis0-recording-scale-bounds/INTERPRETATION.md) sealed three complete histories, one partial and two unstarted; broad bounds reach about 1,792 km, narrower sensitivity 477 m. | Tighter nonlinear propagation or supported training-feasible regions, adequate numerical treatment and observational covariance assessment remain open. Shared-scale qualification cannot repair nonlinear width. [Earlier 10/12-fit evidence](ilvis0-prediction-covariance-20261012/RESULTS.md) stays unresolved. |
| V02 | P0 — new fits blocked; saved evidence audited | [Saved prediction audit](ilvis0-saved-prediction-comparison/INTERPRETATION.md) reconciles 18 prior analyses of one recording: 15 originally converged, three unresolved; three matched sets are complete. Specified-field globe retains a much smaller horizontal error, while calibration uncertainty and absolute adequacy remain open. | F01, V01 and qualified solver before new representative predictions. No independent replication or new winner follows from reusing old errors. |
| L01 | P1 — streaming, covariance and sharding qualified | [Structured covariance](ilvis0-structured-error-controls/INTERPRETATION.md) passes at 64,080 epochs/27 columns with a 24 MiB cache. [Long streaming comparison](ilvis0-streaming-precision/INTERPRETATION.md) passes all six controls: 480,000-packet values and all 27 derivatives match unchanged kernels exactly; traced stream working memory stays below 0.7 MiB. [Native-control sharding](native-sharded-execution/README.md) passes all nineteen execution controls and all 24 native compatibility cases. One-thread native arrays match the four-thread reference bit for bit; complete bound reports match exactly. | Preserve earlier exact-pose failure. No active study changes allocation. Software equivalence does not qualify sampling phase, observational covariance, full-record accuracy or predictive adequacy. |
| E01 | P1 — selection/motion assessments and local rate controls complete | [Version 1 inventory](esa-development-selection/README.md) admits no stretches. The [motion diagnostic](esa-motion-diagnostic/INTERPRETATION.md) passes eleven identities. [Rate/body controls](esa-rate-qualification/INTERPRETATION.md) pass all 48 identities under declared sampling hypotheses, preserving original engineering samples. | Receiver-error assessment and motion-model adequacy precede a revised policy. Actual phase/filtering, geographic/whole-record propagation, mounting and lever arms remain open; protected outcomes stay sealed. |
| E02 | P1 — blocked | ESA development comparison, then separately frozen confirmation on reserved groups. | C04, V02, L01, E01. Freeze model, uncertainty, adequacy, selection and numerical rules before protected model evaluation. |
| G01 | P1 — descriptive companion complete | [All 53 raw-gyro comparisons](ilvis0-gyro-companion-v2/INTERPRETATION.md) follow 48 independent controls. Median absolute rate differences: 0.88°/h specified-field globe, 2.84°/h zero-field globe, 5.87°/h level flat; all 243 fixed scenarios per stretch are preserved. | No fitted gyro correction or fused-attitude subtraction. Unknown aircraft motion/mounting/processing remain; 27 conservative groups are not independent-flight counts. Preserve the prior technical failure and both freezes; no rerun. |
| U01 | P1 — development metadata complete; final dataset pending | [Immutable version 2](PAPER_DATASET.md) retains 53 stretches, 318 latest primaries, 791 history records, 27 conservative groups and gyro baselines; all 326 catalog entries and all history origins are reconciled. Publication and numerical-operation environments remain separate. | Qualified prediction errors, independent confirmation and calibrated uncertainty remain V02/E02/U02 requirements before the final seal. Unknown diagnostic-point ancestry remains explicit; version 1 is preserved. |
| U02 | P1 — blocked | Calibrate the shape-first decision and subsequent field comparison at the flight-group level. | V02, E02, U01 and separately frozen finite calibration design; include correlated errors, nuisance fitting and minimum over globe candidates. |
| R01 | Follow-on — deferred | Freely measured retained background vector and geographic patterns. | C04 and V02; audit geographic/installation rank before fitting. [Field plan](ROTATION_FIELD.md). |
| R02 | Follow-on — deferred | Solar/sidereal precision comparison with freely fitted rate. | R01 plus supported clock/gain/bias precision and longer records; no inference from a fixed-rate candidate. |
| S01 | Secondary — deferred | Wuhan independent positions/eligibility and stationary-consumer physical validation. | Separate dataset-specific qualification; no automatic transfer of archive thresholds. |
| D01 | Supporting | Exact instrument/processing documentation and defensible calibration alternatives. | Supporting work, not a blanket reason to suspend analysis. |

The execution order is F01/F02, C02/C03/C04, V01/V02, L01/E01/E02,
G01, then U02. U01 is assembled throughout. Cheap software and metadata
prerequisites may precede a blocked stage without consuming protected outcomes.

The current whole-box prediction construction fails the recording-scale
usefulness gate. Preserve its sealed time-limit outcome; do not extend it or
start dependent aircraft fits. G01 is now complete under its recorded orientation
limitations. U01's second development snapshot completes the acquisition-flow and
operation/environment indices. L01's short and long reference comparisons now
qualify streaming equivalence; its first exact-pose failure is preserved and
reproduces identically in the unchanged kernel. The next ready software task
addresses [joint calibration structure and nonlinear remainder growth](ilvis0-native-training-contraction/JOINT_PLAN.md):
the [affine support component](ilvis0-affine-support-qualification/INTERPRETATION.md)
now passes all 24 identities. The complete
[generated orientation cover](ilvis0-orientation-cover/INTERPRETATION.md)
passes all 48 sectors while retaining the original range, but reduces widths
only twofold to fourfold and misses its tenfold target.
[Shared-clock controls](ilvis0-correlated-clock-controls/INTERPRETATION.md)
now pass all 24 identities and 2,774 exact oracle points.
[Regrouped native propagation](ilvis0-regrouped-controls/INTERPRETATION.md)
passes all 24 qualification identities and all 162 tangent-column checks.
The complete [regrouped orientation comparison](ilvis0-regrouped-cover/INTERPRETATION.md)
passes all 48 sectors. Widths improve further but remain about 115 m per axis
for globe cases and miss the unchanged tenfold target. The
[saved-constraint audit](ilvis0-regrouped-constraint-audit/INTERPRETATION.md)
passes all 48 sectors: stronger linear projection leaves 25 of 27 ranges
unchanged, and every nonlinear height floor exceeds the target.
[Shared-reference native controls](ilvis0-shared-native-controls/INTERPRETATION.md)
now pass all 24 identities and 162 tangent-column checks, retaining the original
physical domain. The [joint 27-plus-6-coordinate interface](ilvis0-shared-envelope-controls/INTERPRETATION.md)
passes all 18 controls. The complete
[shared-reference orientation comparison](ilvis0-shared-cover/INTERPRETATION.md)
passes all 48 sectors and the tenfold target in all six cases: typical globe
widths fall from about 115 m to 31 m per axis at 1.8 seconds. The
[duration-growth screen](ilvis0-shared-duration-growth/INTERPRETATION.md)
passes all 48 identities: unshared width contributions grow from about 15 m to
150 m between 1.8 and 7.2 seconds, almost entirely through position propagation.
The [common reference-acceleration component](ilvis0-reference-acceleration-controls/INTERPRETATION.md)
passes 18 identities, 1,152 probes and 4,608 polynomial checks. Its
[separate native construction](ilvis0-reference-acceleration/NATIVE_PLAN.md)
passes its [24-identity native qualification](ilvis0-acceleration-native-controls/INTERPRETATION.md)
and all 162 tangent-column checks. The [42-column joint interface](ilvis0-acceleration-envelope-controls/INTERPRETATION.md)
passes all 19 controls. The complete
[common-acceleration comparison](ilvis0-acceleration-cover/INTERPRETATION.md)
passes all 48 sectors: all six cases meet the unchanged target, with complete
axis widths of 0.061–0.358 m at 1.8 seconds, versus roughly 31 m previously.
The [acceleration-aware duration screen](ilvis0-acceleration-duration-growth/INTERPRETATION.md)
passes all 48 identities. At 7.2 seconds the largest unshared contribution is
1.164 m, versus about 150 m previously. Both execution qualifications now pass.
The [longer complete comparison](ilvis0-longer-acceleration-cover/INTERPRETATION.md)
passes all 48 sectors at 7.2 seconds. Complete widths are 0.620–2.973 m,
growing 8.27–12.47 times when time increases fourfold. Next audit the saved
training constraints and affine/nonlinear contributions before another larger run.
The [saved certificate audit](ilvis0-longer-prediction-audit/README.md) passes
all 48 cases and 288 exact checks. Nonlinear allowances account for 37.8–42.1%
of individual widths; position propagation supplies at least 94.9% of that
portion. [Full 42-coordinate projection](ilvis0-joint-constraint-projection-v2/README.md)
passes all 48 cases and 4,032 proposals: initial velocity, position and three
auxiliary acceleration-error ranges tighten; 21 physical and 12 auxiliary ranges
remain materially unchanged. A separately frozen future-bound-only comparison
[passes all 48 cases](ilvis0-projected-future-bounds/INTERPRETATION.md), but
widths improve only 0.4–2.9%, to 0.616–2.889 m. Further coordinate searches are
deprioritized; next diagnose accumulation of the position-propagation allowance
without changing arithmetic or physical assumptions. The
[propagation observer](ilvis0-propagation-trace/INTERPRETATION.md) now passes
all six cases with exact report equality. Its force-difference action is the
largest observed force-action remainder. The next ready component preserves
[a common calibration transform across changing force samples](ilvis0-common-force-transform/PLAN.md);
its [component qualification](ilvis0-force-transform-controls/INTERPRETATION.md)
now passes all 24 controls, 1,536 probes and 6,144 weighted-map identities.
The [common-clock integral qualification](ilvis0-force-clock-controls/INTERPRETATION.md)
also passes all 24 controls and 1,728 exact G/H checks.
The [native common-transform qualification](ilvis0-transform-native-controls/INTERPRETATION.md)
now passes all 24 matched controls, including 78 native evaluations and 348 bounds
under unchanged numerical limits. The [typed 51-column joint interface](ilvis0-transform-envelope-controls/INTERPRETATION.md)
also passes all 36 controls, including every new matrix-error column and
source/future-input rejection. The
[complete 7.2-second prediction comparison](ilvis0-transform-cover/INTERPRETATION.md)
now passes all 48 sectors. Widths narrow by 40–66%, but only three of six
model/processing groups meet the unchanged twofold target on every axis.
The [saved-evidence audit](ilvis0-transform-prediction-audit-v2/README.md)
passes all 48 cases and 288 exact support checks; its initial zero-start
import failure is preserved. The
[calibration-consistency component](ilvis0-calibration-consistency-controls/README.md)
now passes all 24 controls, 9,216 exact inequalities and 4,608 matrix-column
checks. The [saved-only comparison](ilvis0-consistent-prediction/INTERPRETATION.md)
passes all 48 cases and 288 independent support checks, but widths improve only
0.1–0.7%; the overall twofold target remains unmet. Further searches of this
relationship are deprioritized. The next component audits and qualifies
[vector-norm information lost when shared errors become coordinate boxes](ilvis0-consistent-prediction/NEXT_PLAN.md),
before another saved comparison or duration expansion. It must establish the
actual norm bounds rather than infer them from equal component caps.
Long-record usefulness, numerical
enclosure and observational coverage remain separate gates; new aircraft
prediction fits remain blocked.
The [shared training-only error assessment](ilvis0-receiver-scale-assessment/INTERPRETATION.md)
completed all six predeclared calculations on one recording. Its scale upper
bounds range from 0.309 to 5.463 across fixed reference/covariance choices;
the Gaussian law remains assumed, and these are not receiver-accuracy measurements. The
[exact-arithmetic prerequisite](ilvis0-exact-scale-v2/INTERPRETATION.md) now passes
all 16 controls, including 292-epoch prefixes; its earlier output-conversion
failure is preserved. The
[native contraction](ilvis0-native-training-contraction/INTERPRETATION.md) passes
all six correctness controls but narrows only two coordinates and leaves future
ranges hundreds of metres wide. Its earlier affine prerequisite passes all 24
identities. New observed prediction fits stay blocked. The connected native source passes
all [24 frozen interface controls](ilvis0-native-source-qualification/README.md),
preserving fixed coordinates, every nuisance column and abstention for missing
global bounds. Useful nonlinear envelopes and training-only seed/fit provenance
remain separate gates.
ESA local rate/body controls are complete under explicit sampling hypotheses;
its zero-eligible selection and protected outcomes remain unchanged.
V01 development may separately investigate
tighter nonlinear propagation and a shared training-only covariance assessment;
the existing eight-family shared-scale controls cannot establish either alone.

### Where earlier unfinished plans belong

| Existing design or unresolved requirement | Backlog home |
|---|---|
| [Channel-removal requirements](ilvis0-measurement-contribution/CHANNEL_CONTROLS.md), calibration ambiguity and failed nonlinear matrix | C02's mathematical controls and C03/C04's descriptive assessments are complete. Stronger gyro attribution and uncertainty remain V01/V02 work. Preserve every earlier failure. |
| [Error-budget next gate](ilvis0-channel-error-budget-20261019/NEXT_PLAN.md): timing, quantization, averaging, support and joint uncertainty | C03; deterministic count/period and direction-cone bounds are checked, the combined observational model is not. |
| [Shared error-model design](ilvis0-residual-covariance-20261012/ERROR_MODEL_PLAN.md), bounded uncertainty and earlier incomplete prediction studies | V01/V02, L01 and U02; reuse their controls, not completed start allowances. |
| [ESA selection proposal](external-imu-data/ELIGIBILITY_PLAN.md) and rate/axis/lever-arm qualification | E01, with F02 reservation enforced before any development or confirmation fit. |
| Raw gyro geographic-prediction companion, residual trends and shared-recorder comparisons | G01 and V02; no fused-attitude substitution or independent-vote counting. |
| Free vector/latitude/rate/altitude follow-ups and [solar/sidereal precision](ROTATION_FIELD.md) | R01/R02 after contribution and prediction qualification. |
| Wuhan independent GNSS processing, consumer physical controls and exact device documentation | S01/D01; retained as separate secondary/supporting work. |

## What is already complete

- Main numerical recovery is retired: all 53 required comparisons are complete.
- The height-score sensitivity work is complete. IMU8 repeats pass; the IMU21
  sensitivity remains unresolved after its finite timing search. Implausible
  unscored heights prevent treating horizontal fits as full-flight adequacy.
- The channel controls include 18 independent exact-trajectory cases, 22
  receiver-derivative/covariance checks, 46 error-budget identities, nine
  constant-gain ambiguity checks and 72 local calibration cases.
- A small constant gain erases straight-leg scalar separation. Changing motion
  retains local differences, but wrong-model linear corrections exceed bounds.
  The later certificate candidate now qualifies all 72 mathematical comparisons;
  C03 uncertainty and timing still precede real-recording interpretation.
- Earlier residual, clock, calibration and split-recording studies remain
  development evidence. Their failed or incomplete outcomes are preserved.

[Study index](STUDIES.md) · [Contribution evidence](ilvis0-measurement-contribution/README.md) ·
[Earlier development history](ANALYSIS_HISTORY.md).

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
