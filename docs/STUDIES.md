# Studies and what each added

**All 53 selected airborne stretches favor globe in the complete full-position
comparison.** The studies below explain how that result was obtained and what
has been checked since. Repeated fits and overlapping recorders do not create
additional independent flights.

An **IMU (inertial measurement unit)** contains gyroscopes and accelerometers.
The gyroscope record measures turning; receiver positions and acceleration
constrain the reconstructed track.

[Verified current findings](CURRENT_STATUS.md) ·
[All 53 stretches](ilvis0-current-findings-20261015/STRETCHES.md) ·
[Comprehensive CSV](ilvis0-current-findings-20261015/stretch-analytics.csv) ·
[Next analyses](NEXT_STEPS.md).

## From recordings to the complete comparison

| Study or stage | What it added |
|---|---|
| [Reference inspection](research-next-stage-20261006/airborne-sample-ilvis0/README.md) and [physical decoding](ilvis0-physical-validation-20261007/README.md) | Recovered intact packet framing, raw angle/velocity increments, units, signs and embedded receiver output. |
| [Other IMU configurations](ilvis0-imu21-assessment-20261007/README.md) and [IMU6 checks](ilvis0-imu6-cross-date-20261007/README.md) | Kept instrument-specific conversion hypotheses separate rather than assuming one format for every file. |
| [Recording screening](ilvis0-retention-84-20261007/README.md) and [motion screening](ilvis0-motion-61-20261007/README.md) | Recorded keep, reject and unsupported outcomes; 232 originals were retained. |
| [Receiver extraction](ilvis0-observation-20261007/README.md) and [GPS checks](ilvis0-gnss-v2-20261007/README.md) | Separated raw inertial observations and primary-receiver positions from the fused navigation solution. |
| [Frozen eligibility inventory](ilvis0-highspeed-segments-20261008/ELIGIBILITY.md) | Selected 53 complete, steady stretches lasting at least four minutes at 700 km/h or faster, before model fitting. |
| [First selected-stretch run](ilvis0-highspeed-segments-20261008/FINDINGS.md) | Completed twelve globe preferences and left 41 numerical comparisons unfinished. |
| [Numerical recovery and final review](ilvis0-last-review-20261018/README.md) | Resolved all 41 using separately checked methods while preserving the observations, physical assumptions and earlier failures. |
| [Combined findings](CURRENT_STATUS.md) | Count each stretch once: **53 globe, zero flat, zero unresolved**; all also prefer the specified background field over zero. |

The [detailed study history](STUDY_HISTORY.md) preserves every intermediate
recovery stage and the approaches that did not qualify.

## What drives the separation?

| Check | What it added or left open |
|---|---|
| [Raw gyroscope overview](ilvis0-gyro-overview/README.md) | Visualizes the same-sign accumulated pitch motion in all selected stretches; it is not a separate curvature test. |
| [Raw gyro geographic companion](ilvis0-gyro-companion-v2/INTERPRETATION.md) | All 53 stretches are compared with precomputed course/latitude/transport/field predictions after 48 independent controls. Median rate differences are 0.88°/h, 2.84°/h and 5.87°/h for specified-field globe, zero-field globe and level flat, without fitted gyro corrections; unresolved aircraft motion remains explicit. |
| [Residual and calibration audit](ilvis0-calibration-audit-20261010/README.md) | Found a large in-sample fitting-error gap on the original twelve stretches, alongside frequent calibration parameters at their bounds. |
| [Refitted clock comparison](ilvis0-clock-trial-20261010/README.md) | All six fits completed and preserved globe/field preferences after changing the timing convention and reoptimizing. |
| [Calibration grid](ilvis0-z-profile-audit-20261011/README.md) and [replication audit](ilvis0-z-followup-audit-20261012/README.md) | Tested gain, bias and processing alternatives; preserved complete comparisons and unresolved grid nodes separately. |
| [Saved coordinate-subset scores](ilvis0-receiver-projection-20261018/README.md) | All 36 horizontal-only processing-case comparisons favor globe at existing parameters; no refit or channel isolation was performed. |
| [First horizontal-only refits](ilvis0-horizontal-repeat-audit-20261019/INTERPRETATION.md) | One of two stretches passed all repeats and favored globe; the other remained unresolved. Unscored height paths were implausible. |
| [Matched timing search](ilvis0-horizontal-multistart-20261019/INTERPRETATION.md) | Passed 37/38 individual fits and both controls, but only 2/6 selected repeat comparisons; the IMU21 sensitivity result remains unresolved. |
| [Channel-removal controls](ilvis0-measurement-contribution/CHANNEL_CONTROLS.md) | Passed 25 software checks and defined an acceleration-only diagnostic without fused attitude; recorded-data qualification remains ahead. |
| [Independent trajectory-force controls](ilvis0-channel-trajectory-controls-20261019/INTERPRETATION.md) | All 18 mathematical controls passed; exact-trajectory acceleration comparisons can separate some generated cases without gyroscopes. |
| [Receiver-derivative checks](ilvis0-channel-trajectory-controls-20261019/DERIVATIVES.md) | Passed 22 unit checks for derivatives, joint covariance, overlapping-window dependence and covariance symmetry. |
| [Approximation and averaging controls](ilvis0-channel-error-budget-20261019/INTERPRETATION.md) | Completed 46 implementation checks and preserved 27/108 approximation-screen failures; quantified polynomial bias, nonlinear magnitude bias and aggregation effects. |
| [Acceleration calibration ambiguity](ilvis0-measurement-contribution/CALIBRATION.md) | Nine known-answer checks show that small constant gain changes erase scalar model separation on a constructed straight leg; changing geometry needs a full-calibration check. |
| [Changing-motion calibration matrix](ilvis0-scalar-calibration-controls-20261019/INTERPRETATION.md) | All 72 local controls pass with seven calibration directions. Changing motion retains local differences, while wrong-model linear corrections exceed bounds; bounded nonlinear checks remain. |
| [Provenance and confirmation reservation](analysis-provenance/README.md) | Records conservative split groups and protects unmodeled ESA groups before fitting; does not infer independent flight or instrument counts. |
| [Bounded nonlinear calibration](ilvis0-scalar-nonlinear-controls-20261019/INTERPRETATION.md) | Completes 228 mathematical starts: 12/12 known-answer starts pass, but only 32/72 matrix comparisons qualify; no observed fitting follows. |
| [Feasible scalar calibration](ilvis0-scalar-certificate-controls-20261019/INTERPRETATION.md) | Qualifies all 72 mathematical comparisons using 147 feasible certificates and 81 actual optimizer starts; preserves uninformative matches and the earlier failed method. |
| [Quantization and period bounds](ilvis0-measurement-contribution/QUANTIZATION.md) | Passes 17 checks of deterministic packet-mean bounds while retaining unresolved averaging, calibration and timing assumptions. |
| [Force-direction averaging bounds](ilvis0-measurement-contribution/FORCE_AVERAGING.md) | Eleven checks bound within-packet averaging under a declared direction-rate envelope and retain an unavailable upper bound when that assumption is absent or unsupported. |
| [Common time support and synchronization](ilvis0-measurement-contribution/TIME_SUPPORT.md) | Thirty-four checks preserve whole-packet support and gaps, and bound prediction averaging/common-offset effects under an explicit rate assumption. Recording-specific clock and combined uncertainty remain open. |
| [Receiver-trajectory truncation bounds](ilvis0-measurement-contribution/DERIVATIVE_BOUNDS.md) | Thirteen checks propagate declared higher-derivative and coordinate-error bounds, retaining all nine estimated components and polynomial-reproduction defects. |
| [Nonlinear force-box propagation](ilvis0-measurement-contribution/FORCE_BOUNDS.md) | Thirty checks propagate coordinate-jet, gravity and field intervals, including independent Cartesian references across all candidates and six motion types. |
| [Combined deterministic error budget](ilvis0-measurement-contribution/COMBINED_BOUNDS.md) | Adds fifteen calibrated-increment and six independent end-to-end checks; 126 checks now cover the component chain. Physical hypotheses still need frozen observational assessment. |
| [Recorded acceleration-only snapshots](ilvis0-channel-envelopes-20261019/INTERPRETATION.md) | All 144 scalar cases overlap on six fixed windows from two recordings. The complete comparisons favor globe; this reduced necessary constraint excludes none and does not establish a feasible whole-history fit. |
| [Whole-history acceleration-only constraints](ilvis0-channel-history-v2-20261019/INTERPRETATION.md) | Extends to 763 packet groups with identical measurements under both clocks. All 27,468 scalar cases overlap and one zero-calibration point survives all 24 history variants; full gyro-free trajectory feasibility remains unproved. |

On the original twelve completed comparisons, median horizontal in-sample errors
were about **0.068 m** for specified-field globe, **29.5 m** for zero-field globe
and **47.1 m** for flat. These figures are not prediction accuracy on unused data,
and they are not summaries of all 53 stretches.

The [measurement-contribution overview](ilvis0-measurement-contribution/README.md)
connects these checks and explains why removing a scored coordinate is different
from removing a sensor observation.

## Prediction, uncertainty and independence

| Check | What it added or left open |
|---|---|
| [Structured covariance and scaling](ilvis0-structured-error-controls/INTERPRETATION.md) | Matches dense references and passes at 64,080 epochs/27 columns with a 24 MiB filter cache; avoids whole-record dense covariance/projection matrices. Observational error assessment remains. |
| [Native streaming equivalence](ilvis0-streaming-precision/INTERPRETATION.md) | All 42 short controls pass; six separate long controls match unchanged value/tangent kernels through 480,000 packets with under 0.7 MiB traced working memory. The earlier absolute-pose failure reproduces identically in the original kernel and remains preserved. |
| [Bounded prediction uncertainty](ilvis0-bounded-prediction-controls/README.md) | All eight frozen software checks pass: 3,072 generated cases retain boundary and unidentified calibration uncertainty, and a 64,080-epoch forecast uses a 23 MiB cache. Archive error assumptions and native approximation bounds remain unqualified. |
| [Training-only prediction interface](ilvis0-bounded-prediction-controls/NATIVE_INTERFACE.md) | Seventeen checks connect supplied predictions and all nuisance columns to the structured calculation, preserving shared scale and global-bound identities. No native integration or observed-data qualification is claimed. |
| [Connected native prediction source](ilvis0-native-source-qualification/README.md) | All 24 frozen identities match unchanged native values and every derivative exactly. Fixed frames and abstention for absent nonlinear bounds are preserved; training-only provenance and useful uncertainty remain open. |
| [Conservative training constraints](ilvis0-training-box-qualification/INTERPRETATION.md) | All 24 frozen identities preserve 784 exact-rational feasible points, all nuisance columns and unchanged weak regions. Native usefulness and scientifically justified input allowances remain. |
| [Native training-region contraction](ilvis0-native-training-contraction/INTERPRETATION.md) | All six controls retain the known truth, but only two coordinates narrow and future ranges remain hundreds of metres wide. Correctness does not pass the usefulness gate. |
| [Saved prediction comparison](ilvis0-saved-prediction-comparison/INTERPRETATION.md) | Reconciles 18 prior analyses of one flight without refitting: three complete matched settings retain a large horizontal globe-with-field advantage. Unfinished fits, growing errors and uncalibrated uncertainty remain visible. |
| [Exact shared-error arithmetic](ilvis0-exact-scale-v2/INTERPRETATION.md) | Sixteen controls pass, including exact matrix agreement and full training-length prefixes. Establishes the calculation under a declared Gaussian law, not actual receiver accuracy. The first version's output failure is preserved. |
| [Training-only receiver-error source](ilvis0-receiver-scale-assessment/INTERPRETATION.md) | Six predeclared calculations complete using earlier GPS positions alone. Bounds depend on the reference path and assumed correlation law; no model can enlarge them through its own residuals. No new Earth-model fit or empirical accuracy claim. |
| [Joint affine support](ilvis0-affine-support-qualification/INTERPRETATION.md) | Twenty-four controls preserve coupled calibration information using exact certificates. This improves the mathematical building block; broad native nonlinear remainders remain the next problem. |
| [Complete orientation cover](ilvis0-orientation-cover/INTERPRETATION.md) | All 48 sectors preserve correctness and retain the original range. Widths improve twofold to fourfold, below the tenfold target; identifies a common-clock cancellation loss. |
| [Shared packet-clock controls](ilvis0-correlated-clock-controls/INTERPRETATION.md) | Twenty-four controls and 2,774 exact oracle points preserve the cancellation lost by independent packet bounds, supplying the clock component for the regrouped construction. |
| [Regrouped native propagation](ilvis0-regrouped-controls/INTERPRETATION.md) | All 24 controls and 162 tangent-column checks pass, preserving the physical candidates and every calibration direction. |
| [Regrouped orientation cover](ilvis0-regrouped-cover/INTERPRETATION.md) | All 48 sectors remain correct. Typical globe widths fall to about 115 m per axis, still short of the tenfold target; the saved constraint audit addresses the remaining loss. |
| [Saved calibration-constraint audit](ilvis0-regrouped-constraint-audit/INTERPRETATION.md) | All 48 audits pass without native integration. Stronger linear projection leaves 25 of 27 ranges unchanged; the nonlinear height allowance itself blocks the target. |
| [Shared-reference native controls](ilvis0-shared-native-controls/INTERPRETATION.md) | All 24 controls and 162 tangent-column checks pass while preserving the physical models and their original calibration bounds. Six bounded common-error coordinates must remain linked across measurement times. |
| [Joint shared-error interface](ilvis0-shared-envelope-controls/INTERPRETATION.md) | Twelve known-answer and six rejection controls pass, preserving one common error block across training and future times and retaining all 33 columns. |
| [Shared-reference orientation comparison](ilvis0-shared-cover/INTERPRETATION.md) | All 48 sectors pass; all six unions meet the tenfold improvement target. Typical globe widths fall from about 115 m to 31 m per axis, still a short generated test rather than aircraft prediction coverage. |
| [Shared-reference duration screen](ilvis0-shared-duration-growth/INTERPRETATION.md) | All 48 identities pass at three horizons. The unshared contribution grows from about 15 m at 1.8 seconds to 150 m at 7.2 seconds, chiefly in position propagation; this directs the next algebraic refinement. |
| [Common acceleration component](ilvis0-reference-acceleration-controls/INTERPRETATION.md) | All 18 identities, 1,152 probes and 4,608 polynomial checks pass against an independent rotation/force formula. Component identity and native propagation are qualified separately. |
| [Common acceleration through native propagation](ilvis0-acceleration-native-controls/INTERPRETATION.md) | All 24 identities and 162 tangent-column comparisons pass without changing the physical models or their bounds. |
| [Complete common-error interface](ilvis0-acceleration-envelope-controls/INTERPRETATION.md) | All 19 controls pass, preserving both common blocks and every physical/auxiliary column across training and future epochs. |
| [Common-acceleration complete comparison](ilvis0-acceleration-cover/INTERPRETATION.md) | All 48 sectors pass; all six cases meet the unchanged target. Complete generated prediction widths fall to 0.061–0.358 m at 1.8 seconds, compared with roughly 31 m previously. Longer-duration usefulness remains open. |
| [Common-acceleration duration screen](ilvis0-acceleration-duration-growth/INTERPRETATION.md) | All 48 identities pass at three horizons. The largest unshared contribution at 7.2 seconds falls from about 150 m to 1.164 m; a longer complete training-constrained comparison remains required. |
| [Global calibration and rotating-force bounds](ilvis0-increment-remainders/INTERPRETATION.md) | All 30 component identities pass against independent matrix-exponential references, including shared calibration across packets. Bounds cover their declared boxes; full midpoint/geographic prediction, timing and long-record rounding remain open. |
| [Native midpoint local-step bounds](ilvis0-local-step-bounds/INTERPRETATION.md) | All 30 generated cases pass against the unchanged C kernel and independent value/derivative references. The bounds preserve Coriolis and removal distinctions; geographic predictor/corrector, endpoint and timing closure remain. |
| [Geographic-step and antenna bounds](ilvis0-geographic-step-bounds/INTERPRETATION.md) | All 72 generated controls pass for the full predictor/corrector, antenna position and 27 native derivative columns. Repeated packets, timing across packet boundaries, long-record arithmetic and observational error assessment remain. |
| [Short histories and boundary timing](ilvis0-history-bounds/INTERPRETATION.md) | All 54 generated controls pass across repeated packets and boundary-crossing time intervals. Full-box remainder allowances reach about 12.54 m; recording-scale usefulness, numerical error and observational covariance remain open. |
| [Recording-scale bound growth](ilvis0-recording-scale-bounds/INTERPRETATION.md) | Three complete four-minute histories pass their numerical comparisons, one is partial and two unstarted at the finite time limit. Global nonlinear allowances become too wide for useful predictions, even under the narrower sensitivity box. |
| [Shared-reference scale bound](ilvis0-shared-reference-scale/INTERPRETATION.md) | All eight generated families/8,192 assessments pass for one shared scale reference that may have an incorrect mean. Covariance shape and aircraft coverage remain assumptions; this does not reduce nonlinear prediction width. |
| [Individual-epoch residuals](ilvis0-residual-diagnostic-20261010/README.md) and [covariance audit](ilvis0-residual-covariance-20261012/README.md) | Exposed temporal correlation and clock sensitivity; small fitting errors alone do not calibrate confidence. |
| [Reserved-time prediction trial](ilvis0-prediction-trial-20261011/RESULTS.md) | Five of six fits completed; the combined prediction comparison remained unfinished. |
| [Training/prediction covariance trial](ilvis0-prediction-covariance-20261012/RESULTS.md) | Ten of twelve fits completed; it did not establish calibrated predictive coverage. |
| [Shared-flight diagnosis](ilvis0-shared-leg-diagnosis-20261014/README.md) | Distinguished simultaneous-recorder agreement from numerical stopping differences and identified overlapping observations. |
| [Development evidence dataset](PAPER_DATASET.md) | Version 2 freezes selections, 318 latest primaries, all 791 history records and their operation environments, plus the reconciled 326-entry acquisition census. Failed work and open validation gates remain visible; the final paper dataset is pending. |

These studies provide development evidence. A calibrated significance level,
absolute predictive adequacy and independent-replication count remain open.

## Separate sources and experiments

| Work | Present scope |
|---|---|
| [ESA and Wuhan data](external-imu-data/README.md) | Longer raw recordings have been inspected, but neither source has entered the Earth-model comparison. |
| [ESA receiver-only selection](esa-development-selection/README.md) | The first frozen policy admits no stretches from development recording 187. Motion exclusions dominate; every rejected run and epoch reason is preserved, with no model fitting or protected-outcome inspection. |
| [ESA rate/body qualification](esa-rate-qualification/INTERPRETATION.md) | All 48 generated identities pass for analytic quadrature and local changing-axis/force bounds. Actual sampling/processing and whole-record geographic propagation remain open; no selection or model result changed. |
| [ESA motion-screening diagnostic](esa-motion-diagnostic/INTERPRETATION.md) | Qualifies the calculation on 24 analytic paths and 2,304 generated cases, then checks 2,048 fixed receiver centers. Adjacent differences are noise-sensitive, but smoothing alone does not establish quiet flight; no selection is changed. |
| [Free rotation-field study](ROTATION_FIELD.md) | Planned measurement of field direction and magnitude, followed by a solar/sidereal precision assessment; no free-rate result is claimed. |
| [Stationary crowdsourcing](STATIONARY.md) | A developing consumer-IMU reversal experiment; its diagnostic does not issue scientific detections. |

Historical simulated-flight campaigns and software trials remain available in
the [detailed history](STUDY_HISTORY.md). Their thresholds do not transfer to
these observations or to the stationary experiment.

[Parallel execution qualification](native-sharded-execution/qualification/README.md): all nineteen controls pass, including twelve real worker launches; no native integrations or observed fits. One-thread scientific compatibility is a separate gate.

[One-thread native compatibility](native-sharded-execution/native-qualification/README.md): all 24 cases pass, with exact native predictions, all 27 derivatives and complete factored-bound reports. Four workers each use one numerical thread; no observed fits.

[Longer complete prediction comparison](ilvis0-longer-acceleration-cover/INTERPRETATION.md): all 48 sectors pass at 7.2 seconds. Complete widths are 0.620–2.973 m, 8.27–12.47 times their 1.8-second values; no observed fits or uncertainty calibration.

[Saved longer-prediction audit](ilvis0-longer-prediction-audit/README.md): all 48 cases and 288 exact support checks pass. Nonlinear allowances contribute 37.8–42.1% of individual widths; no new integrations or fits.

[Full joint-coordinate projection](ilvis0-joint-constraint-projection-v2/README.md): all 48 cases and 4,032 proposals complete; velocity, position and three shared-acceleration ranges tighten. The [initial zero-start loading failure](ilvis0-joint-constraint-projection/INTERPRETATION.md) is retained separately.

[Future bounds after projection](ilvis0-projected-future-bounds/INTERPRETATION.md): all 48 cases pass, but complete widths improve only 0.4–2.9%. This limits further coordinate-search work and directs the next diagnostic toward propagation accounting.

[Propagation accounting observer](ilvis0-propagation-trace/INTERPRETATION.md): all six cases reproduce the prior reports exactly. The largest force-action allowance follows changing force samples, directing the next common-transform derivation.

[Common force-transform component](ilvis0-force-transform-controls/INTERPRETATION.md): all 24 controls pass, checking 1,536 probes, 1,296 independent derivatives and 6,144 map identities. Integrated clock dependence and native/joint use remain separate gates.

[Common-clock force integration](ilvis0-force-clock-controls/INTERPRETATION.md): all 24 controls pass, including 1,728 exact integral checks. Matrix/clock cross terms and exported-coefficient rounding remain explicit; native use is still gated.

[Native common-transform qualification](ilvis0-transform-native-controls/INTERPRETATION.md): all 24 controls pass with 78 native evaluations and 348 bounds under unchanged numerical limits. Typed joint prediction and complete-range usefulness remain separate gates.

[Joint 51-column interface](ilvis0-transform-envelope-controls/INTERPRETATION.md): all 36 controls pass with 126 LP proposals and 252 exact certificates. All nine force-error columns, source consistency and absent future receiver input are checked.

[Complete common-transform comparison](ilvis0-transform-cover/INTERPRETATION.md): all 48 generated sectors pass correctness at 7.2 seconds. Widths shrink 40–66%, but three of six groups miss the fixed twofold target. No new aircraft fits.

[Saved common-transform audit](ilvis0-transform-prediction-audit-v2/README.md): all 48 cases and 288 independent rational support checks pass. The earlier zero-start import failure is preserved. Checks qualify internal consistency, not aircraft-error coverage.

[Calibration consistency](ilvis0-calibration-consistency-controls/README.md): all 24 controls, 9,216 exact inequalities and 4,608 matrix-column checks pass. The necessary constraints preserve physical bounds and tie existing error coordinates to one calibration; prediction usefulness remains a separate gate.

[Prediction with consistent calibration](ilvis0-consistent-prediction/INTERPRETATION.md): all 48 saved cases and 288 independent endpoint/support checks pass without new native calculations. Complete widths narrow only 0.1–0.7%; the overall twofold target remains unmet.

[Shared vector-norm qualification](ilvis0-shared-norm-controls/README.md): all 24 controls pass, checking 1,536 physical probes, 10,752 vector bounds and 279,552 exact inequalities. Seven shared error vectors retain their proven norm limits; this does not yet establish narrower predictions.

[Prediction with shared vector norms](ilvis0-norm-prediction/INTERPRETATION.md): all 48 saved cases and 288 independent support checks pass, but complete widths improve by less than 0.1%. The fixed twofold target remains unmet; no longer prediction or aircraft fitting follows.

[Rotation/gain supports](ilvis0-rotation-gain-controls/README.md): all 24 controls and 119,808 exact inequalities pass. Matrix columns retain necessary directional bounds tied to their calibration gains; a separate saved-case comparison tests usefulness.

[Prediction with rotation/gain supports](ilvis0-rotation-gain-prediction/INTERPRETATION.md): all 48 cases and 288 independent support checks pass. Horizontal ranges narrow 1–3%, while height ranges remain unchanged; the fixed target is still unmet.

[Exact feasible-witness controls](ilvis0-feasible-witness-controls/README.md): twenty known-answer cases pass with all 51 coordinates. Exact repairs verify every constraint and preserve boundary collapse; these witnesses describe a relaxation, not necessarily a physical calibration.

[Prediction-range diagnosis](ilvis0-relaxed-width-audit/INTERPRETATION.md): all six saved cases supply exactly checked examples. Their widths are within 0.00000214 m of the existing upper bounds; better optimization alone cannot meet the failing targets under this construction.

[Extreme-matrix check](ilvis0-matrix-gram-audit/INTERPRETATION.md): all 36 tested extreme examples fail a necessary rotation condition, while all six physical anchors pass. This identifies impossible combinations admitted by the uncertainty method; it does not yet establish narrower valid predictions.

[Orientation-aware matrix constraints](ilvis0-orientation-gain-controls/INTERPRETATION.md): all 24 controls pass, preserving 1,536 physical probes and 119,808 new inequalities. The constraints retain the allowed orientation range; prediction usefulness is tested separately.

[Prediction with orientation constraints](ilvis0-orientation-gain-prediction/INTERPRETATION.md): all 48 sectors and their endpoint checks pass, but complete ranges improve by less than 0.2%. The fixed target remains unmet; no new aircraft fits follow.

[Separate column-motion bounds](ilvis0-column-orientation-controls/INTERPRETATION.md): all 24 controls pass, including 1,536 physical probes and 119,808 new support checks. Pure axial rotation correctly leaves its own column unchanged; complete prediction usefulness is tested separately.

[Prediction with separate column bounds](ilvis0-column-orientation-prediction/INTERPRETATION.md): all 48 sectors pass correctness, but ranges improve by at most 0.016%. The fixed target remains unmet; the next diagnostic isolates internal error blocks before further refinement.

[Internal error-block diagnosis](ilvis0-error-block-ablation/INTERPRETATION.md): all 24 known-value-assisted cases pass numerical checks. No single block dominates the width. The report discloses 144 extra source-certificate checks beyond the declared allowance; this is diagnosis, not qualification.

[Training-derived acceleration bounds](ilvis0-acceleration-projection/INTERPRETATION.md): all six cases pass exact checks and reduce the acceleration-change radius by about 92–93%. Bounds use training information only. Propagation and complete prediction usefulness still need testing.

[Propagation with training-derived acceleration](ilvis0-conditioned-native-controls/INTERPRETATION.md): all six longer native controls pass, preserving centers, derivatives, shared coefficients and known-probe containment. Unshared position bounds narrow about 3–19%; a complete sector comparison is next.

[Background-subtracted gyro visualization](ilvis0-background-subtracted/README.md): the same 53 raw traces remain nose-down after subtracting the specified field's level/course projection. It is a descriptive display using GPS for the correction, with aircraft motion retained and no new fit.

[Prediction with training-conditioned acceleration](ilvis0-conditioned-prediction/INTERPRETATION.md): all 48 sectors pass correctness, and four of six groups meet the unchanged width target. Both specified-field globe groups remain above it. All 576 LP proposals and 2,304 exact supports reconcile with sealed reservations; no observed fit follows.

[Joint rotation-product constraints](ilvis0-rotation-product-controls/INTERPRETATION.md): all 24 cases retain 1,536 sealed physical probes under 198,144 exact inequality checks. Arithmetic products relate matrix columns without adding physical parameters; complete prediction usefulness remains a separate test.

[Prediction with joint rotation relationships](ilvis0-product-prediction/INTERPRETATION.md): all 48 sectors pass correctness and all charges reconcile. Widths improve by less than 0.1%, leaving four of six groups passing; further linear matrix variations are deprioritized in favor of checking the complete calibration map.

[Complete calibration-map diagnosis](ilvis0-calibration-map-diagnostic/INTERPRETATION.md): all 36 allowed extremes fail after their common errors are recomputed from one calibration. Six known controls reproduce exactly; this identifies loose error bookkeeping without supplying a narrower certified prediction range.

[ESA position-based motion qualification](esa-position-motion/INTERPRETATION.md): all ten identities pass, covering 24 analytic paths and 2,304 noisy realizations. Treating correlated errors as independent undercovers badly; real receiver assessment and the unchanged zero-eligible selection remain separate.

[ESA matched position/velocity assessment](esa-position-assessment/INTERPRETATION.md): checks all 2,048 fixed centers and identifies 96 quiet-trend intervals under arbitrary temporal correlation. It improves the uncertainty check without establishing continuous quiet flight or changing the zero-eligible inventory.

[Complete coupled calibration map](ilvis0-coupled-map-controls/INTERPRETATION.md): all 24 source/domain controls pass 1,158 value and independent derivative checks plus 1.61 million scalar inequalities. Prediction usefulness still requires the next complete comparison.

[Complete coupled-map prediction comparison](ilvis0-coupled-prediction/INTERPRETATION.md): all 48 sectors pass correctness, but widths improve by less than 0.12% and four of six groups still pass the target. The saved decomposition supports testing smaller calibration boxes before recomputing native bounds.

[Smaller calibration-box comparison](ilvis0-coupled-subdivision/INTERPRETATION.md): all 192 checks pass, but ranges narrow by at most 1.26% and four of six groups still meet the target. This rules out the tested mounting-angle subdivision as a sufficient remedy.

[Saved prediction-endpoint audit](ilvis0-coupled-subdivision/ENDPOINT_DIAGNOSIS.md): exact accounting of all 36 union endpoints identifies substantial training and future propagation allowances. It uses saved evidence only and directs the next test toward those allowances.

[Training-remainder diagnostic](ilvis0-training-remainder-diagnostic/INTERPRETATION.md): six bounds finish; smaller domains change height allowances by less than 0.003%. A saved-only audit resolves the adapter's coefficient-unit mismatch while preserving its original failed labels. No aircraft fit or future prediction ran.

[Direction-preserving rotation bound](ilvis0-directional-rotation/README.md): 12 local checks, including 384 independent numerical rotations, support an exact unit-axis bound that preserves the difference between yaw and tilt. It is a component test, not a qualified replacement for full propagation.

[Calibrated directional-force controls](ilvis0-directional-force-controls/INTERPRETATION.md): all 24 cases and 1,158 independent probes pass. Static height ranges are about 9–31% as wide as the old norm-based ranges; usefulness in an integrated trajectory remains to be tested.

[Directional native propagation controls](ilvis0-directional-native-controls/INTERPRETATION.md): all 24 matched cases pass, using 78 native evaluations and 348 bounds. Original center, derivative, stationary-pose and containment criteria remain; the complete prediction comparison is a separate gate.

[Directional prediction comparison](ilvis0-directional-prediction/INTERPRETATION.md): 39 sectors pass before the time ceiling; four starts are interrupted and five remain unstarted. All four complete globe groups keep their inherited widths. A saved audit identifies loss of tighter training-derived bounds; this method does not pass the width gate.

[Componentwise dynamic-value prototype](ilvis0-directional-dynamics/README.md): twelve local tests preserve separate coordinate changes and Taylor remainders through four vector operations. This starts a direction-aware dynamic method; complete matrix/rotation propagation is not yet qualified.

[Matrix and rotation-identity controls](ilvis0-directional-dynamics/OPERATOR_DERIVATION.md): the prototype reaches 33 local checks covering matrix actions, exact polynomial curves, scalar domains and norm-preserving departures. Source and reference-coefficient qualification remain necessary before native integration.

[Source-level norm preflight](ilvis0-source-norm-preflight/INTERPRETATION.md): all six controls pass against the actual body-rotation baseline while retaining training-derived force bounds. Vertical value widths retain about 5.6–6.3% of the old width; native reference coefficients and propagation remainders remain unqualified.

[Source reference and affine-error comparison](ilvis0-source-reference/INTERPRETATION.md): all six groups pass the 27-column reference check, and usable vertical source error allowances shrink by 68–69%. Complete dynamic propagation remains the next gate; no aircraft refits ran.

[Direction-preserving force action](ilvis0-directional-dynamics/SOURCE_ACTION.md): five local checks qualify an operator that retains component bounds and all 27 affine columns, including coefficient-rounding allowances. Complete velocity and coordinate propagation remain to be integrated.

[Coordinate-preserving native transport](ilvis0-component-transport-controls/INTERPRETATION.md): 20/24 controls pass; four long globe bounds reach the unchanged time limit. The failed qualification remains preserved.

[Cached coordinate transport](ilvis0-cached-transport-controls/INTERPRETATION.md): all 24 native controls pass, preserving exact coordinate/norm bounds and all physical/shared columns. The next step is connecting the tighter body-source interval before a complete prediction comparison.

[Streaming source references](ilvis0-source-stream-controls/INTERPRETATION.md): all six generated sources pass 3,225,600 midpoint/end comparisons with a fixed 10,768-byte working state. This supplies the explicit rows needed for source integration.

[Body-interval prototype](ilvis0-body-interval/README.md): ten local tests check training-conditioned bounds around explicit reference rows, including deliberately changed rows and contradictory-interval rejection. Complete native integration remains unqualified.

[Saved-baseline transport screen](ilvis0-transport-range-preflight/README.md): four compatible full-history bounds and two time-limit failures; the completed specified-field cases tighten east allowances by about 3.4% and height by about 10%. All six attempts and 36 support verifications remain accounted for.

[Transport runtime profiles](ilvis0-transport-runtime-profile/INTERPRETATION.md): both shortened probes complete and identify repeated exact-arithmetic bound operations as major costs. A compiled backend must retain conservative bounds and pass exact-reference checks before longer comparisons.

[Compiled native transport](ilvis0-compiled-transport-controls/INTERPRETATION.md): all 24 controls pass, with unchanged acceptance limits, reference centers and 51-column expansions. The six-source long-history screen is the next gate; no aircraft refits ran.

[Compiled long-history screen](ilvis0-compiled-range-preflight/INTERPRETATION.md): all six source comparisons pass in 244 seconds, resolving the two earlier timeouts while preserving reference maps and training constraints. Complete prediction widths remain unqualified.

[Source point-domain check](ilvis0-body-interval/POINT_DIAGNOSIS.md): a fixed-parameter regression exposes a missing reference-rounding allowance. Source integration remains blocked until that error is explicitly bounded; physical assumptions and aircraft results are unchanged.

[Rotation-center error component](ilvis0-body-interval/ROUNDING_PLAN.md): eight local checks compare exact-rational rotation enclosures with an independent matrix series, including zero, subnormal and eight-radian inputs. Complete source-reference rounding is still unqualified.

[Calibration-reference error component](ilvis0-body-interval/ROUNDING_PLAN.md): five local checks cover exact bias/gain intervals, increment/rate conversion and errors in supplied reference centers and rows. These primitives still need integration into the complete source bound.

[Physical source-value qualification](ilvis0-source-value-controls/INTERPRETATION.md): all six sources pass 115,200 comparisons and 19,200 norm closures across every packet phase. The next gate transfers the saved training constraint to the separate rounded adapter.

[Rounded trained-source qualification](ilvis0-rounded-source-controls/INTERPRETATION.md): all six sources pass 1,440 known-calibration checks after 120 bounds are sealed, preserving the original training certificates, centers, rows and nonlinear caps. Full native integration is next.

[First integrated source trial](ilvis0-source-native-controls/INTERPRETATION.md): 18/24 controls pass; all six broad cases stop at a cap check. The saved-input diagnosis identifies an unnecessarily symmetric calibration box; a new candidate must qualify on the unchanged original domains and caps.

[Revised integrated source trial](ilvis0-source-native-v2-controls/INTERPRETATION.md): all 24 native controls pass using the actual calibration boxes and unchanged caps, centers, 51 columns and acceptance limits. Comparison with the best saved compatible ranges is next.

[Installed-source range screen](ilvis0-source-range-preflight/INTERPRETATION.md): two cases complete and four reach the time limit; the completed cases tighten height allowances while widening horizontal ones. Runtime and source-specific Taylor information need further work; aircraft results are unchanged.

[Installed-source runtime profiles](ilvis0-source-runtime-profile-v2/INTERPRETATION.md): both shortened generated-data probes complete and locate substantial repeated interface costs. These profiles do not qualify long-history performance or prediction widths.

[Batched native calculation](ilvis0-batched-native-controls/INTERPRETATION.md): all 24 controls pass and all 348 bounds exactly match the predecessor. Recorded runtime falls from 201 to 92 seconds with the same four-thread allocation; long-history performance and complete prediction widths remain separate checks.

[Batched full-history screen](ilvis0-batched-range-preflight/INTERPRETATION.md): all six cases complete within the original limits. Height allowances shrink by 17–37%; horizontal allowances remain wider, so source-derivative bounds are next. No aircraft findings change.

[Source derivative component](ilvis0-source-derivative-v2-controls/INTERPRETATION.md): all ten independent known-answer controls pass, including calibration signs, reference rounding and both clock-boundary slopes. Native integration and useful complete prediction widths remain separate gates.

[Native source-derivative calculation](ilvis0-taylor-native-controls/INTERPRETATION.md): all 24 controls pass. Across 348 bounds, predictions, coefficient matrices and physical bindings are unchanged, and error allowances do not widen. A full-history comparison is next.

[Source-derivative long-history screen](ilvis0-taylor-range-preflight/INTERPRETATION.md): all six cases pass; profiled-processing horizontal allowances improve by 6–11%, while tighter fixed-zero baselines remain in use. A saved audit verifies training ancestry in all 48 narrower domains; checked subdomain transfer and the complete prediction-width comparison are next.

[Complete source/domain preflight](ilvis0-complete-source-preflight/INTERPRETATION.md): all 48 regions retain their verified training bounds and pass the initial-source cap check. The joint prediction path and complete width comparison remain to be qualified.

[Complete joint-adapter controls](ilvis0-taylor-joint-controls/INTERPRETATION.md): all six known-answer model/processing cases pass, including training-conditioned bounds, subdomain transfer, full coefficient preservation and final truth checks. The complete 48-region prediction comparison is next.

[Complete source-derivative prediction comparison](ilvis0-taylor-complete-prediction/INTERPRETATION.md): 32 of 48 regions pass and 16 reach time limits. Completed specified-field groups gain 25–28% narrower height ranges, but their horizontal ranges still miss the target. Runtime and horizontal error-budget diagnosis follow; no aircraft findings change.

[Source-derivative runtime diagnostic](ilvis0-taylor-runtime-profile/INTERPRETATION.md): both short profiles complete and identify repeated exact-fraction source-bound calculations as a substantial cost. An exact integer implementation will be checked against the original arithmetic before a new performance study.

[Exact integer native qualification](ilvis0-dyadic-native-controls/INTERPRETATION.md): all 24 controls pass, reproducing all 348 saved bounds exactly. A small matched timing test precedes any new full-history performance screen; no speedup or new aircraft result is claimed.

[Matched implementation timing](ilvis0-dyadic-timing/INTERPRETATION.md): all four calculations complete with exact output agreement. The integer implementation is 9–11% faster on the two short sources; full-history performance remains a separate check.

[Saved prediction-width audit](ilvis0-taylor-complete-prediction/WIDTH_AUDIT.md): all 96 available per-region axis widths reconstruct from their saved support ranges and approximation allowances. This is a metadata-only decomposition; missing regions and scientific findings remain unchanged.

[Full-history integer implementation screen](ilvis0-dyadic-range-preflight/INTERPRETATION.md): all six actual child-domain queries complete within the original time limit; the three available predecessor bounds match exactly. Runtime is improved, while the complete prediction-width gate remains unmet.

[Current saved endpoint diagnosis](ilvis0-taylor-complete-prediction/ENDPOINT_DIAGNOSIS.md): all 18 fresh endpoints of the three complete groups reproduce exactly. Training and future propagation allowances dominate the difficult eastward endpoints; no new integration or optimization ran.

[Propagation tracing qualification](ilvis0-traced-native-controls/INTERPRETATION.md): all 24 controls pass, preserving all 348 checked native bounds. The finite eight-query diagnostic will trace the fixed endpoint sectors without changing the calculations.

[Eastward allowance growth](ilvis0-eastward-growth/INTERPRETATION.md): six traces match exactly and two reach time limits. The accumulated departure accounts for about 81–85% of the completed queries' final eastward allowance; source and clock bounds are the next mathematical targets. These are generated approximation bounds, not aircraft measurement errors.

[Direct source-remainder components](ilvis0-source-remainder-v2-controls/INTERPRETATION.md): all 13 mathematical controls pass, including calibration, clipped-clock and noncommuting rotation cases. Numerical-reference reconciliation and native usefulness remain open; the earlier wrapper failures are preserved.

[Point-source derivatives](ilvis0-source-point-controls/INTERPRETATION.md): all seven controls pass against separate rational values and all 27 derivative columns, including clock knots. Combining the component bounds and qualifying full native predictions remain open.

[Combined direct source bound](ilvis0-direct-source-controls/INTERPRETATION.md): all five controls pass against independent rational chains, including shifted numerical references and broad gain domains. Full native installation and prediction usefulness remain unqualified.

[Direct-source native qualification](ilvis0-direct-native-controls/INTERPRETATION.md): all 24 controls pass, preserving the maps and not widening any of 348 bounds. A saved-only audit verifies the extra point/source work; full-history usefulness is the next gate.

[Direct-source full-history screen](ilvis0-direct-range-preflight/INTERPRETATION.md): all six cases pass under the original time limit, with 25–50% smaller horizontal approximation allowances. The complete prediction-width comparison remains ahead.

[Direct-source complete adapter](ilvis0-direct-joint-controls/INTERPRETATION.md): all six known-answer cases pass, including training-row and future-endpoint audits.

[Direct-source width comparison](ilvis0-direct-complete-prediction/INTERPRETATION.md): 36/48 regions pass; twelve future bounds time out. Three groups have complete ranges meeting the target, while three remain incomplete. Compatible saved-certificate reuse is the next proposed check; neither failed study is relabeled.

[Saved-certificate adapter](ilvis0-reused-joint-controls/INTERPRETATION.md): all 12 known-answer cases pass, including missing-new-provider cases, without integration.

[Complete saved-bound comparison](ilvis0-reused-complete-prediction/INTERPRETATION.md): all 40 calculations pass in 139 seconds with no integration reruns; four of six complete final covers meet the fixed width target. The two specified-field cases miss only the east-coordinate target, by 3.4% and 2.5%. Recording-scale uncertainty remains open.

[East-coordinate width diagnosis](ilvis0-east-width-audit/INTERPRETATION.md): all 32 saved support checks reproduce; older future bounds supply three of four limiting endpoints, making their missing tighter replacements the next runtime target. No new integration or model fit ran.

[Direct-source cost profile](ilvis0-direct-source-cost-profile/INTERPRETATION.md): all six unchanged source streams complete in 74 seconds; physical-value certificates dominate the measured source cost. A midpoint-only candidate passes 19 focused equivalence checks; a speedup remains unproven.

[Midpoint-only native qualification](ilvis0-midpoint-native-controls/INTERPRETATION.md): all 24 cases pass; all 348 reports, including every error-allowance array, match the predecessor exactly. Runtime usefulness is tested separately.

[Matched complete-domain timing](ilvis0-midpoint-runtime/INTERPRETATION.md): only two of six pairs finish; four hit the original time limits. Exact agreement survives in completed pairs, but the shortcut does not qualify for a replacement-future rollout.

[Whole-bound profile](ilvis0-whole-bound-profile/INTERPRETATION.md): the unchanged specified-field bound completes on one thread in 89.4 profiled seconds, identifying costs beyond source construction and motivating a separate serial execution check.

[Serial execution screen](ilvis0-serial-bound-screen/INTERPRETATION.md): all six unchanged bounds complete in 38–41 seconds each and reproduce every saved report field exactly. The qualified recipe uses one worker and one numerical thread.

[Missing serial future certificates](ilvis0-serial-future-bounds/INTERPRETATION.md): all twelve queries pass in 689 seconds without recalculating training bounds. A new saved-only complete-cover comparison must still assess the fixed width target.

[Three-source reuse controls](ilvis0-reused-three-controls/INTERPRETATION.md): all twelve known-answer cases pass in 15.45 seconds, preserving numerical operations while checking the three studies' provenance. The all-region width rebuild has its own freeze.

[Complete three-source width rebuild](ilvis0-three-source-complete/INTERPRETATION.md): all 48 regions and all six complete covers pass the original width target in 258 seconds. Completed training bounds are reused; recording-length usefulness and the observation-error model remain open.

[Four-minute input compatibility](ilvis0-recording-adapter-controls/README.md): all six cases match predictions, all 27 derivative columns and warning flags exactly across the two software interfaces; this checks data handling, not prediction uncertainty or independent physical truth.

[Longer-input bound growth](ilvis0-recording-growth-screen/INTERPRETATION.md): all six numerical cases complete in 38.5 minutes; 71–72 km unconstrained outer radii remain too wide, and a smaller approximation remainder does not improve the total range in the matched historical cases.

[Accumulated inertial-error component](ilvis0-inertial-error-controls/INTERPRETATION.md): all 28 software checks pass against an independent continuous-time reference, adding an explicitly assumed IMU-noise contribution alongside receiver error; the real observation-error law remains unqualified.

[Explicit training-error interface](ilvis0-recording-training-interface/INTERPRETATION.md): all 15 focused checks pass, requiring longer studies to declare each observation allowance instead of inheriting the short example's fixed 1 mm.
