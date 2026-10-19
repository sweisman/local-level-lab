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
| C02 | P0 — qualification incomplete | [Nonlinear calibration outcome](ilvis0-scalar-nonlinear-controls-20261019/INTERPRETATION.md): 12/12 known-answer starts pass, but only 32/72 matched comparisons pass every repeat check. | All 228 starts completed; 80 endpoints exhausted budget near small residuals. No resume. A separate candidate must handle flat/near-zero directions before observed use. |
| C03 | P0 — initial bounds checked | [17 quantization/period controls](ilvis0-measurement-contribution/QUANTIZATION.md) pass; synchronization, within-packet averaging, combined uncertainty and common support remain. | C01. Deterministic bounds do not shrink as independent noise or establish continuous-force upper bounds. |
| C04 | P0 — blocked | Finite matched gyro-free necessary-constraint versus complete-observation comparison on preselected recordings. | F01, C02, C03 and new-objective solver qualification. Freeze identities and costs before launch. Non-identifiability is a valid outcome. |
| V01 | P0 — pending | Shared residual covariance and bounded nuisance uncertainty fitted on training data only. | F01; reuse completed software controls and residual audits. Qualify parameter/covariance uncertainty, not only local linear covariance. |
| V02 | P0 — blocked | Representative NASA blocked predictions and supported cross-flight transfer, with absolute three-axis adequacy. | F01, V01 and qualified solver. Freeze splits, initialization dependencies and adequacy criteria before prediction evaluation. |
| L01 | P1 — pending prerequisite | Structured covariance and matrix-free residual/Jacobian whitening; streaming/block integration with preserved state. | Match dense small-problem references and benchmark long-record memory/runtime. Required before long ESA fits, not short NASA controls. |
| E01 | P1 — pending | ESA-specific eligibility inventory, rejection reasons and qualified rate/acceleration adapter. | F02; implement the existing [selection proposal](external-imu-data/ELIGIBILITY_PLAN.md) as its first version. Keep all protected outcomes sealed. |
| E02 | P1 — blocked | ESA development comparison, then separately frozen confirmation on reserved groups. | C04, V02, L01, E01. Freeze model, uncertainty, adequacy, selection and numerical rules before protected model evaluation. |
| G01 | P1 — pending | Companion gyro-prediction plot: course/latitude/mount/transport/field versus observed signed variation. | F01 and explicit orientation provenance. Preserve raw plot; expose aircraft motion and mount/crab ambiguity rather than using fused attitude to remove them. |
| U01 | P1 — pending | Versioned paper dataset with grouping, selections, hashes, fits, prediction errors, exclusions and abstentions. | F01; assemble incrementally. Seal final version after C04, V02 and E02. |
| U02 | P1 — blocked | Calibrate the shape-first decision and subsequent field comparison at the flight-group level. | V02, E02, U01 and separately frozen finite calibration design; include correlated errors, nuisance fitting and minimum over globe candidates. |
| R01 | Follow-on — deferred | Freely measured retained background vector and geographic patterns. | C04 and V02; audit geographic/installation rank before fitting. [Field plan](ROTATION_FIELD.md). |
| R02 | Follow-on — deferred | Solar/sidereal precision comparison with freely fitted rate. | R01 plus supported clock/gain/bias precision and longer records; no inference from a fixed-rate candidate. |
| S01 | Secondary — deferred | Wuhan independent positions/eligibility and stationary-consumer physical validation. | Separate dataset-specific qualification; no automatic transfer of archive thresholds. |
| D01 | Supporting | Exact instrument/processing documentation and defensible calibration alternatives. | Supporting work, not a blanket reason to suspend analysis. |

The execution order is F01/F02, C02/C03/C04, V01/V02, L01/E01/E02,
G01, then U02. U01 is assembled throughout. Cheap software and metadata
prerequisites may precede a blocked stage without consuming protected outcomes.

### Where earlier unfinished plans belong

| Existing design or unresolved requirement | Backlog home |
|---|---|
| [Channel-removal requirements](ilvis0-measurement-contribution/CHANNEL_CONTROLS.md), calibration ambiguity and failed nonlinear matrix | C02/C04; preserve completed controls and qualify a separate candidate before observed use. |
| [Error-budget next gate](ilvis0-channel-error-budget-20261019/NEXT_PLAN.md): timing, quantization, averaging, support and joint uncertainty | C03; initial deterministic quantization bounds are complete, the combined observational model is not. |
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
  That is why C02 precedes real-recording interpretation.
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
