# What comes next

All **53 preselected airborne stretches favor globe geometry** in the completed
full-position comparison. All also prefer the specified background rotation
field over zero. The next work tests what produces that separation and how well
it predicts measurements excluded from fitting.

An **IMU (inertial measurement unit)** measures turning with gyroscopes and
specific force with accelerometers. Gyroscopes are the turning observations;
receiver positions and accelerometers constrain the reconstruction.

[Current findings](CURRENT_STATUS.md) · [All stretches](ilvis0-current-findings-20261015/STRETCHES.md) ·
[Comprehensive CSV](ilvis0-current-findings-20261015/stretch-analytics.csv).

<a id="then-strengthen-the-interpretation"></a>

## The next milestones

| Order | Work | What it should establish |
|---|---|---|
| Foundation — recorded | [Shared-flight ledger and confirmation reservation](analysis-provenance/README.md). | The 53 stretches form 27 conservative split groups, not verified independent flights. ESA recording 187 is development material; seven other groups are protected for confirmation. |
| First | Finish the [measurement-contribution comparison](ilvis0-measurement-contribution/README.md). | Show what the gyro adds beyond receiver positions, acceleration and declared assumptions. Report where the gyro-free comparison is legitimately uninformative. |
| Next | Predict observations excluded from fitting. | Estimate calibration and error assumptions on training data, then test all three position components, including height. Better than another model is not enough: the prediction must also be physically adequate. |
| Then | Qualify a separate [ESA replication](external-imu-data/README.md). | Test different survey hardware and processing with its own slower-flight eligibility and protected confirmation groups. Scalable covariance and integration are prerequisites for long fits. |
| Companion | Compare the raw gyro variation with declared predictions. | Explain course, latitude, mounting, transport and background-field contributions; preserve unresolved aircraft motion rather than hiding it. |
| Publication | Establish flight-level uncertainty and freeze the evidence dataset. | Account for shared observations, nuisance fitting, correlated errors and the complete shape-first decision procedure before calibrated detection claims. |

The [technical roadmap](ANALYSIS_ROADMAP.md) is the authoritative backlog,
with task IDs, dependencies and completion gates. Detailed reports preserve the
development evidence; they do not create additional execution queues.

## Current diagnostic gate

The independent force and receiver-derivative controls are complete, along with
the approximation/averaging matrix. A small permitted acceleration-gain change
can erase straight-leg scalar separation. The
[72-case local calibration matrix](ilvis0-scalar-calibration-controls-20261019/INTERPRETATION.md)
retains changing-motion differences, but its wrong-model linear corrections
exceed the bounds.

The [bounded nonlinear study](ilvis0-scalar-nonlinear-controls-20261019/INTERPRETATION.md)
passed all 12 known-answer starts but qualified only 32/72 matched comparisons;
near-zero, weakly determined cases still exhausted the solver allowance. The
observed channel comparison remains blocked. Initial [quantization/period checks](ilvis0-measurement-contribution/QUANTIZATION.md)
pass; synchronization, averaging and combined uncertainty still need treatment.
These checks precede a finite matched real-recording comparison. Fused navigation cannot replace
an omitted gyro measurement. Matching acceleration magnitudes alone does not
establish a complete gyro-free reconstruction.

The earlier horizontal-only sensitivity study stays separate: one IMU8 comparison
passes its repeats, while the IMU21 sensitivity remains unresolved. Without
scoring height, even repeatable fits can predict implausible altitude. Further
timing searches are deferred. The main 53-stretch result is unchanged.

## Development predictions and independent confirmation

NASA blocked predictions can withhold observations from fitting, but the archive
has already informed development. Those tests are retrospective development
validation, not untouched confirmation.

The unmodeled ESA flight groups are reserved before fitting. Integrity checks
and receiver-only eligibility screening may proceed. Model evaluation waits
until selection, physical/error assumptions, numerical checks and adequacy rules
are frozen. Shared files and simultaneous instruments do not supply independent
replications.

## Later work

The [rotation-field study](ROTATION_FIELD.md) will fit the retained field's size,
direction and geographic pattern freely after measurement-contribution and
prediction checks. Only supported precision can then test **15.0000 versus about
15.0411 degrees/hour**. The present fixed-rate comparison has not measured that
difference or identified the field's cause.

Wuhan source development and the [stationary consumer experiment](STATIONARY.md)
remain separate, lower-priority branches. Exact instrument documentation is
supporting work, not a blanket prerequisite for modeling with stated assumptions.
The consumer analyzer continues to abstain from scientific decisions until
physical sensitivity and uncertainty are validated.

[Method](METHODOLOGY.md) · [Studies](STUDIES.md) · [Diagnostic requirements](ILVIS0_DIAGNOSTIC_PLAN.md).
