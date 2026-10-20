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
| Companion — complete | [Raw gyro variation beside geographic predictions](ilvis0-gyro-companion-v2/INTERPRETATION.md). | All 53 stretches, 48 independent controls and 243 declared scenarios per stretch. The specified-field globe is closest on the median-rate difference; aircraft-motion and processing contributions remain unresolved. |
| Publication — development metadata complete | [Evidence dataset](PAPER_DATASET.md), then flight-level uncertainty. | Version 2 reconciles all 326 catalog entries and all 791 history records, including operation environments. Predictive adequacy, independent confirmation and calibrated decisions remain. |

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

The first bounded nonlinear study qualified only 32/72 matched comparisons.
A separate [feasible-calibration candidate](ilvis0-scalar-certificate-controls-20261019/INTERPRETATION.md)
now passes all 12 known-answer identities and 72/72 comparisons, recognizing
near-zero scalar matches explicitly. These are mathematical controls, not
airborne findings. The observed channel comparison remains blocked by the
measurement-error gates. Initial [quantization/period checks](ilvis0-measurement-contribution/QUANTIZATION.md)
pass, as do eleven [force-direction averaging checks](ilvis0-measurement-contribution/FORCE_AVERAGING.md).
The averaging bound requires an explicit continuous direction-rate assumption.
Another [34 common-support and timing checks](ilvis0-measurement-contribution/TIME_SUPPORT.md)
now pass, preserving whole packets and bounding common-offset effects under a
declared magnitude-rate envelope. Thirteen additional
[derivative-error checks](ilvis0-measurement-contribution/DERIVATIVE_BOUNDS.md)
pass under declared higher-derivative bounds. Thirty
[nonlinear force-box checks](ilvis0-measurement-contribution/FORCE_BOUNDS.md)
also pass. The [combined deterministic chain](ilvis0-measurement-contribution/COMBINED_BOUNDS.md)
now passes 126 component/end-to-end checks. The frozen
[two-recording snapshot assessment](ilvis0-channel-envelopes-20261019/INTERPRETATION.md)
is complete: all 144 scalar cases overlap, with no unsupported cases. It excludes
none of the candidates under the declared assumptions. The
[whole-history continuation](ilvis0-channel-history-v2-20261019/INTERPRETATION.md)
now covers 763 packet groups: all 27,468 scalar cases overlap and one fixed zero
calibration survives all 24 history variants. This still does not establish a
complete gyro-free reconstruction or quantitative gyro attribution.
The next work is training-only covariance and nuisance uncertainty, followed by
withheld prediction; scalable covariance operations support both.

The [structured covariance prerequisite](ilvis0-structured-error-controls/INTERPRETATION.md)
now matches dense controls and passes at 64,080 epochs with 27 Jacobian columns,
using a 24 MiB cache. It handles a supplied error model; estimation uncertainty
remains a separate requirement. The
[streaming integrator](ilvis0-streaming-precision/INTERPRETATION.md) now matches
the unchanged value and 27-column derivative kernels through 480,000 packets,
with under 0.7 MiB of traced stream working allocation.

The [bounded prediction method](ilvis0-bounded-prediction-controls/README.md) keeps
one shared error assessment across candidates, retains unidentified calibration
directions and requires explicit nonlinear-remainder treatment. Its eight frozen
software checks now pass, including 3,072 generated cases and a 64,080-epoch
forecast. This qualifies the calculation under its declared error assumptions;
it does not establish their accuracy for the aircraft records. The
[new interface](ilvis0-bounded-prediction-controls/NATIVE_INTERFACE.md) passes
17 checks of training-only inputs, complete calibration bounds and fixed
coordinate transforms. The [next gate](ilvis0-bounded-prediction-controls/NEXT_PLAN.md)
now has [global increment components](ilvis0-increment-remainders/INTERPRETATION.md):
all 30 frozen identities pass for calibration, rotation and body preintegration.
The [actual midpoint local step](ilvis0-local-step-bounds/INTERPRETATION.md) now
also passes all 30 generated cases against the unchanged C kernel. Its
[geographic predictor/corrector and antenna closure](ilvis0-geographic-step-bounds/INTERPRETATION.md)
also passes all 72 controls, including all 27 native derivative columns and
timing inside a packet. The [54 short-history controls](ilvis0-history-bounds/INTERPRETATION.md)
also pass, including time intervals crossing packet boundaries. Broad calibration
regions yield remainder allowances around twelve metres even on these short
controls; they are not measured errors. The [recording-scale study](ilvis0-recording-scale-bounds/INTERPRETATION.md)
completed three four-minute histories, with a fourth partial and two unstarted
when its finite clock allowance ended. Broad-region approximation bounds grow
to about 1,792 km; a narrower sensitivity box still gives 477 m. These are
overly conservative bounds, not measured aircraft errors. Tighter nonlinear
propagation or supported training constraints are needed for useful intervals.
The [shared-reference error calculation](ilvis0-shared-reference-scale/INTERPRETATION.md)
now passes eight frozen generated families and 8,192 assessments. It supplies a
common scale bound under a declared Gaussian covariance shape; it neither
establishes that shape for aircraft observations nor fixes nonlinear width.
Another observed-data prediction trial remains blocked. The independent
[gyro-prediction companion](ilvis0-gyro-companion-v2/INTERPRETATION.md) is complete:
all 53 stretches are included without fitted gyro corrections or fused-attitude
subtraction. Orientation assumptions and finite sensitivity scenarios are exposed.
The [second development evidence snapshot](PAPER_DATASET.md) now includes the full
acquisition flow and operation/environment indices. Nonlinear prediction and
observational-error methods still need work; the snapshot makes those gaps explicit
rather than presenting a final validated paper dataset. The
[shared training-only error assessment](ilvis0-receiver-scale-assessment/INTERPRETATION.md)
completed all six predeclared cases on one recording. Its upper bounds depend
strongly on the reference trajectory and assumed covariance; actual receiver
accuracy is not established. Next work returns to
[joint calibration constraints and nonlinear remainder growth](ilvis0-native-training-contraction/JOINT_PLAN.md),
without dropping feasible orientations or using later observations.
Its [exact joint-affine component](ilvis0-affine-support-qualification/INTERPRETATION.md)
passes all 24 identities. The complete
[orientation cover](ilvis0-orientation-cover/INTERPRETATION.md) passes all 48
sectors but misses its improvement target. The
[common packet clock](ilvis0-correlated-clock-controls/INTERPRETATION.md)
passes 24 controls and 2,774 exact oracle points. The
[regrouped native construction](ilvis0-regrouped-controls/INTERPRETATION.md)
also passes all 24 identities and 162 tangent-column checks. Its complete
[regrouped orientation comparison](ilvis0-regrouped-cover/INTERPRETATION.md)
passes all 48 sectors but still misses the tenfold improvement target.
The [saved-constraint audit](ilvis0-regrouped-constraint-audit/INTERPRETATION.md)
now passes all 48 sectors with zero new native evaluations. Linear projection
adds almost no narrowing. The
[shared-reference native construction](ilvis0-shared-native-controls/INTERPRETATION.md)
now passes all 24 controls and 162 tangent-column checks. Its
[joint interface](ilvis0-shared-envelope-controls/INTERPRETATION.md) passes all
18 controls connecting common errors across measurement times. The complete
[shared-reference orientation comparison](ilvis0-shared-cover/INTERPRETATION.md)
passes all 48 sectors and its tenfold target in all six cases. Typical globe
ranges shrink from about 115 m to 31 m per axis at 1.8 seconds. The
[duration screen](ilvis0-shared-duration-growth/INTERPRETATION.md) passes all 48
identities but shows unshared contributions growing to about 150 m at 7.2 seconds,
mainly through position propagation. The
[reference-acceleration component](ilvis0-reference-acceleration-controls/INTERPRETATION.md)
passes all 18 identities. Its [native construction](ilvis0-reference-acceleration/NATIVE_PLAN.md)
passes all [24 native identities](ilvis0-acceleration-native-controls/INTERPRETATION.md)
and 162 tangent-column checks; the [joint interface](ilvis0-acceleration-envelope-controls/INTERPRETATION.md)
passes all 19 controls. The complete
[common-acceleration comparison](ilvis0-acceleration-cover/INTERPRETATION.md)
passes all 48 sectors and the unchanged target: complete widths range from
0.061 to 0.358 m at 1.8 seconds, compared with roughly 31 m previously.
The [acceleration-aware duration screen](ilvis0-acceleration-duration-growth/INTERPRETATION.md)
passes all 48 identities: at 7.2 seconds the largest unshared contribution is
1.164 m, versus about 150 m previously. Execution and exact native compatibility
now pass. The [longer complete comparison](ilvis0-longer-acceleration-cover/INTERPRETATION.md)
passes all 48 sectors at 7.2 seconds, with complete widths of 0.620–2.973 m.
The [saved audit](ilvis0-longer-prediction-audit/README.md) passes all 288 exact
checks. [Full 42-coordinate projection](ilvis0-joint-constraint-projection-v2/README.md)
passes all 48 cases, tightening velocity, position and three common acceleration
coordinates. The [future-bound recomputation](ilvis0-projected-future-bounds/INTERPRETATION.md)
passes all 48 cases but reduces widths only 0.4–2.9%. A focused propagation-
allowance diagnostic now [passes all six cases](ilvis0-propagation-trace/INTERPRETATION.md)
with exact report equality. The next [mathematical component](ilvis0-common-force-transform/PLAN.md)
preserves one calibration transform across changing force samples. Its
[24 component controls](ilvis0-force-transform-controls/INTERPRETATION.md) pass;
the [clock/integral qualification](ilvis0-force-clock-controls/INTERPRETATION.md)
also passes all 24 cases. The [native candidate](ilvis0-transform-native-controls/INTERPRETATION.md)
passes all 24 matched controls. The [joint interface](ilvis0-transform-envelope-controls/INTERPRETATION.md)
passes all 36 checks. The [complete generated comparison](ilvis0-transform-cover/INTERPRETATION.md)
passes all 48 sectors and narrows widths by 40–66%; three of six groups meet
the unchanged twofold target, so the overall usefulness gate remains unmet.
The [independent saved audit](ilvis0-transform-prediction-audit-v2/README.md)
passes all 288 exact support checks. The
[calibration-consistency component](ilvis0-calibration-consistency-controls/README.md)
now passes 24 controls and 9,216 exact inequalities. Its
[saved-only comparison](ilvis0-consistent-prediction/INTERPRETATION.md) passes
all 48 cases but narrows ranges by just 0.1–0.7%, leaving the overall target
unmet. Next, qualify [vector-norm relationships lost in separate coordinate bounds](ilvis0-consistent-prediction/NEXT_PLAN.md)
before another duration expansion. Broader coordinate searches are
deprioritized; no aircraft fits follow yet.
These are software checks, not new aircraft results.
Its [exact-arithmetic prerequisite](ilvis0-exact-scale-v2/INTERPRETATION.md)
passes all 16 controls, without qualifying the assumed Gaussian error law.
The [native contraction](ilvis0-native-training-contraction/INTERPRETATION.md)
passes six correctness controls but leaves ranges hundreds of metres wide;
its 24 affine prerequisite controls remain preserved. This is a limitation of
the current uncertainty construction, not measured aircraft error.
The connected native interface passes
all [24 frozen controls](ilvis0-native-source-qualification/README.md), preserving
fixed coordinates, all nuisance columns and abstention for absent nonlinear bounds. The ESA
[rate/body controls](esa-rate-qualification/INTERPRETATION.md) now pass all 48
generated identities under explicit sampling hypotheses. The streaming
prerequisite is complete: six long controls preserve
the original calculation, while its earlier micrometre-scale exact-pose failure
is reproduced identically in the unchanged kernel and remains documented.
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

The [saved prediction audit](ilvis0-saved-prediction-comparison/INTERPRETATION.md)
reconciles all 18 old analyses of one recording. The specified-field globe
retains a large horizontal advantage after GPS positions are withheld; its
errors still grow to several metres. Three source fits remain unfinished.
No new fit or calibrated adequacy claim is added by this audit.

The [first ESA development inventory](esa-development-selection/README.md) is
complete: no intervals in recording 187 pass the frozen twenty-minute policy.
The longest retained run is about 85 seconds, with motion exclusions dominating.
The [completed receiver-only diagnostic](esa-motion-diagnostic/INTERPRETATION.md)
shows noise sensitivity in adjacent differences, but the smoother trend still
flags substantial motion and its intervals cannot confirm quiet flight under
the reported covariance. Receiver-error assessment and motion adequacy must
precede a separately versioned selection. No ESA Earth-model result is available,
and the original policy remains unchanged.

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
