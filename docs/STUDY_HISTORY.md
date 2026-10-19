# Detailed study history

This page preserves the development record and intermediate outcomes. Historical counts describe their own stage, not the current combined findings. For the present result and priorities, see [current findings](CURRENT_STATUS.md), the [short study index](STUDIES.md) and [next analyses](NEXT_STEPS.md).


The central question is whether recorded aircraft motion fits a globe or the
specified flat disc. An **IMU (inertial measurement unit)** contains gyroscopes and
accelerometers. The gyroscope record is the central turning measurement; GPS
supplies route and timing, with receiver positions also constraining the fitted track.

This page follows the evidence and the problems each study addressed. Related
software checks are grouped together. **[Current verified findings](CURRENT_STATUS.md)**
give the published totals; **[all 53 stretches](ilvis0-current-findings-20261015/STRETCHES.md)**
and the **[comprehensive CSV](ilvis0-current-findings-20261015/stretch-analytics.csv)**
give the individual records. [Further planned work](NEXT_STEPS.md) is separate.

## Establishing usable observations

| Study | What it established or added |
|---|---|
| [Reference-file inspection](research-next-stage-20261006/airborne-sample-ilvis0/README.md) | Established intact packet framing, measurement timing and embedded GPS while preserving the initially unknown IMU payload. |
| [Physical decoding](ilvis0-physical-validation-20261007/README.md) | Independently recovered the reference IMU8 angle and velocity increments, units, axis order and signs. |
| [Timestamp and configuration follow-up](ilvis0-followup-20261007/README.md) | Resolved time conventions and recovered candidate flight windows without choosing them by model agreement. |
| [Other instrument configurations](ilvis0-imu21-assessment-20261007/README.md) and [cross-date IMU6 checks](ilvis0-imu6-cross-date-20261007/README.md) | Tested conversion hypotheses separately instead of applying one instrument's scale to the whole archive. |
| [Installation and clock investigation](ilvis0-installation-clock-20261007/README.md) | Explained changed axis mappings and how fluctuating timestamp intervals can create apparent vertical-force changes. |
| [Screening difficult recordings](ilvis0-retention-84-20261007/README.md) and [remaining motion cases](ilvis0-motion-61-20261007/README.md) | Recorded keep, reject and unsupported outcomes using data quality and motion criteria; the retained corpus contains 232 originals. |
| [Receiver-position extraction](ilvis0-observation-20261007/README.md) and [GPS checks](ilvis0-gnss-v2-20261007/README.md) | Built observation streams from raw IMU increments and receiver output while keeping the fused navigation answer out of the fits. |
| [Fixed eligibility inventory](ilvis0-highspeed-segments-20261008/ELIGIBILITY.md) | Saved all 53 qualifying stretches before fitting: at least four minutes, every supported speed at least 700 km/h, plus completeness and motion checks. |

## What the model comparisons resolved

“Resolved” here means that every required model, processing case, repeat and control
passed its numerical checks. It does not mean that every model fit equally well.
An unfinished calculation provides no finding in favor of either shape.

| Study | What it added | Published outcome at that stage |
|---|---|---|
| [Initial six-recording fits](ilvis0-exploratory-20261008/README.md) | Tried the complete observation model on real recordings. | Finite outputs, but no completed comparisons. |
| [Archive-wide exploration](ilvis0-corpus-modeling-20261008/README.md) | Extended the investigation to retained recordings and exposed numerical and motion-model limitations. | Exploratory fitted/unsupported outcomes, separate from the later fast-level selection. |
| [Six-recording refinement](ilvis0-refinement-20261008/PROVISIONAL.md) | Compared shape first under four instrument/processing assumptions. | Two complete globe preferences; four recordings unresolved. |
| [First full selected-stretch study](ilvis0-highspeed-segments-20261008/FINDINGS.md) | Fitted every preselected stretch under the same two primary processing cases. | **12 globe / 0 flat / 41 unresolved.** |
| [Actual-position stopping qualification](ilvis0-position-stability-trial-20261013/README.md) | Tested stopping using fresh physical position changes while preserving the gradient and cost limits. | All 24 trial fits passed; three recoveries qualified for the wider run. |
| [Full numerical recovery](ilvis0-position-recovery-20261013/README.md) | Applied the qualified method with unchanged measurements and physical bounds. | **30 / 0 / 23**, including those trial recoveries. |
| [Paired-recorder precision trial](ilvis0-paired-precision-trial-20261014/RESULTS.md) | Qualified wider arithmetic on overlapping recorder pairs, with controls and repeats. | **32 / 0 / 21.** |
| [Cost-precision recovery](ilvis0-cost-precision-recovery-20261014/RESULTS.md) | Recovered nine complete comparisons limited by numerical cost precision. | **41 / 0 / 12.** |
| [Budget continuation](ilvis0-budget-continuation-20261014/RESULTS.md) | Tested whether a larger finite allowance resolved three exhausted cases. | No additional complete comparisons. |
| [Remaining precision cases](ilvis0-remaining-precision-20261014/RESULTS.md) | Applied the precision method to the other declared failure classes. | Three more globe preferences: **44 / 0 / 9.** |
| [Matched hybrid-solver trial](ilvis0-trust-trial-20261015/RESULTS.md) | Combined full bounded steps with damped steps on difficult cases. | Two more complete globe comparisons: **46 / 0 / 7**; wider qualification failed. |
| [Six-target hybrid assessment](ilvis0-hybrid-remaining-20261015/RESULTS.md) | Tested the remaining declared targets with their own repeats and passing companions. | One more globe preference: **47 / 0 / 6.** |

These are stages of one developing analysis, **not extra independent datasets**.
The same stretch is counted once in the combined findings. Simultaneous instruments
and shared flights also require grouping before statistical claims.

## Checking why the models differ

The next [measurement-contribution study](ilvis0-measurement-contribution/README.md)
has an input-dependency audit and 19 passing covariance/coordinate-projection
controls. It has not yet run observed ablation fits.

The [saved-primary inventory](ilvis0-contribution-inventory-20261018/COVERAGE.md)
checks all 318 final primary fits. It finds 164 complete reusable artifacts and
eighteen stretches with all six fits ready, while recording every missing array,
time-context gap and unresolved reference. It makes no native predictions or fits.

The [receiver-coordinate projection audit](ilvis0-receiver-projection-20261018/README.md)
compares full, horizontal and height-only constraints at the saved parameters
for those eighteen complete sets. All 36 horizontal-only processing-case
comparisons favor globe; height-only scoring favors globe in 28 and flat in
eight. No parameters were refitted. The original model results remain unchanged.

The [generated-motion refitting qualification](ilvis0-projected-fitting-controls-20261018/README.md)
passed 24 controls before stopping at a failed height-only fit. Eighteen planned
controls remain untested. All six horizontal fits reached so far passed, but
their second-start checks did not run. The candidate is **not qualified** for
observed refits; no recorded-flight result changed.

The [fixed-endpoint diagnostic](ilvis0-projected-endpoint-diagnostic-20261018/INTERPRETATION.md)
used 33 generated-motion evaluations to show that the proposed linear correction
is too large to predict the actual fit reliably. Column rescaling gives the
same result. It identifies a smaller trust-region step as the next candidate,
without performing new fits or changing the failed qualification.

The [complete trust-region control matrix](ilvis0-projected-trust-qualification-20261018/README.md)
passed sixteen of 24 generated fits and eight of twelve paired-start checks.
All twelve horizontal fits passed; eight height-only fits failed the final
full-range stability probe. The [following sequence](ilvis0-projection-sequence-20261018/README.md)
separately tested a local probe with unchanged numerical tolerances: all 24 fits
passed, but one paired-start objective check still failed. The
[larger-budget continuation](ilvis0-projected-budget-continuation-20261018/PLAN.md)
completed both fits in 1,035 native calls but did not resolve the height-only pair.
The [complete review](ilvis0-projected-complete-review-20261018/README.md) remains
unqualified at eleven of twelve passing pairs. Both coordinators completed
without launching their dependent full-calibration matrix.

The [horizontal-only review](ilvis0-projected-horizontal-review-20261018/README.md)
verifies all twelve horizontal fits and all six paired-start comparisons; it
leaves height-only unqualified and preserves the failed broader gate. The subsequent
[horizontal full-calibration study](ilvis0-projected-horizontal-fullcal-20261018/PLAN.md)
tested all 26/27 nuisance columns: eight of twelve fits and three of six paired
comparisons passed, leaving recorded-data refitting blocked.

The [saved correction audit](ilvis0-horizontal-correction-audit-20261018/INTERPRETATION.md)
identified overlarge parameter moves in weak directions. Its separately bounded
[native probe check](ilvis0-horizontal-probe-20261018/README.md) reproduced all
twelve endpoints and passed all twelve regularized proposals without changing
the physical objective or final tolerances. The current
[staged qualification](ilvis0-horizontal-ridge-qualification-20261018/README.md)
passed all eight fits and five of six paired comparisons in 534 native calls.
The [remaining paired continuation](ilvis0-horizontal-pair-continuation-20261018/README.md)
passed both fits and all six combined pairs in 508 native calls, completing
the staged horizontal-only software qualification.

The [first horizontal-only recorded-flight study](ilvis0-horizontal-observed-20261018/README.md)
completed all twelve baseline reconstructions and 24 fits in 1,112 native calls.
The IMU8 stretch passes all six repeats and still favors globe; the IMU21 stretch
passes three of six repeats and remains unresolved in this sensitivity study.
Both starts rank the models the same way. The
[saved-fit audit](ilvis0-horizontal-repeat-audit-20261019/INTERPRETATION.md)
separates competing timing solutions from a marginal prediction-repeat failure
and reports the large unscored height errors. The
[completed 28-point diagnostic](ilvis0-horizontal-repeat-probes-20261019/INTERPRETATION.md)
isolates coupled timing/calibration and an unobserved vertical direction. The
[completed 29-point timing check](ilvis0-horizontal-timing-path-20261019/DIAGNOSIS.md)
finds no gross derivative fault and a path consistent with different locally
stationary solutions, without optimization or label changes.
The original 53/0/0 findings remain unchanged.

The [multi-start qualification](ilvis0-multistart-controls-v3-20261019/README.md)
passed four known-answer systems with coupled calibration, multiple local optima,
active bounds and invisible nuisance coordinates: 24 starts /166 constructed
calls. The [matched recorded-data follow-up](ilvis0-horizontal-multistart-20261019/INTERPRETATION.md)
completed 38 starts /2,376 native calls in 6.59 hours: both controls and 37
individual fits passed, but only two of six selected repeat comparisons passed.
Specified-field globe reproduced its best predictions; the IMU21 sensitivity
comparison remains unresolved. Wider timing searches are deferred while the
separate gyro/acceleration contribution controls are developed.

The [channel-removal controls](ilvis0-measurement-contribution/CHANNEL_CONTROLS.md)
pass 25 known-answer software checks. They expose the orientation freedom left
without gyroscopes and define an acceleration-magnitude diagnostic without using
fused attitude. This is software groundwork, with no new archived-data fits.

| Study | What it solved, tested or left open |
|---|---|
| [Calibration and fit-quality audit](ilvis0-calibration-audit-20261010/README.md) | Found a substantial fitting-error gap on the original twelve resolved stretches, together with frequent calibration parameters at their limits. |
| [Individual-epoch residuals](ilvis0-residual-diagnostic-20261010/README.md) | Exposed time-dependent errors and showed that changing the clock at fixed parameters particularly affects vertical predictions. |
| [Refitted clock comparison](ilvis0-clock-trial-20261010/README.md) and [calibration audit](ilvis0-clock-calibration-audit-20261011/README.md) | All six refitted comparisons completed and preserved globe/field preferences, while calibration readjustment compensated for the clock change. |
| [Z-axis calibration ablation](ilvis0-calibration-trial-20261011/README.md) | Fixing Z gain at zero preserved the preference; fixing Z offset left a required fit unfinished. |
| [Joint gain–offset grid](ilvis0-z-profile-audit-20261011/README.md) | All 27 fits completed and globe/field preferences persisted across the declared Z calibration grid. |
| [Possible onboard field-removal grid](ilvis0-z-profile-removal-20261011/RESULTS.md) | All 27 fits completed and the preferences persisted when a common removed field fraction was allowed. |
| [Second-recording calibration grid](ilvis0-z-profile-replication-20261011/RESULTS.md) and [combined audit](ilvis0-z-followup-audit-20261012/README.md) | Seven complete grid comparisons favored globe; two remained unfinished, preserving the replication's limits. |
| [Within-interval integration trial](ilvis0-integration-trial-20261011/README.md) | Tested an alternative treatment of motion within each IMU interval; four of six fits completed and no replacement qualified. |
| [Reserved-time prediction trial](ilvis0-prediction-trial-20261011/README.md) | Tested observations outside the fitting portion; five of six fits completed, leaving the combined comparison unfinished. |
| [Residual covariance audit](ilvis0-residual-covariance-20261012/README.md) | Found persistent error correlation, showing why small fitting errors alone do not calibrate confidence. |
| [Training/prediction covariance trial](ilvis0-prediction-covariance-20261012/RESULTS.md) | Tested a training-selected error model on reserved observations; ten of twelve fits completed and the combined comparison remained unresolved. |
| [Shared-flight diagnosis](ilvis0-shared-leg-diagnosis-20261014/README.md) | Compared simultaneous recorder tracks and separated agreement in observations from disagreement in numerical stopping. |

The fitting-error audit found median horizontal errors of about **0.068 m** for
the globe with the specified background field, **29.5 m** for zero-field globe and
**47.1 m** for the disc on the same original twelve stretches and two processing
cases. These are in-sample errors under each candidate's declared geometry,
not independent prediction accuracy.

## Finding and testing numerical failure mechanisms

Software controls have known answers. They check the calculations; they do not add
flight evidence. A method that passes them must still be checked on the recordings.

| Study or related checks | What it added |
|---|---|
| [Initial solver trial](ilvis0-solver-trial-20261010/README.md) and [known-answer qualification](ilvis0-solver-qualification-20261010/README.md) | Established software controls, but the observed replacement completed fewer fits than the baseline and did not qualify. |
| [Parameter scaling](ilvis0-unit-scale-trial-20261011/README.md) and [verified stopping](ilvis0-verified-stop-trial-20261011/README.md) | Tested alternative numerical handling without changing physical models; neither supplied a qualified general replacement. |
| [Continuation trial](ilvis0-convergence-recovery-trial-20261012/README.md) and [diagnosis](ilvis0-recovery-diagnosis-20261012/README.md) | Recovered individual fits but no complete test stretch, motivating a different bounded-step method. |
| [Rectangular-method trial](ilvis0-rectangular-recovery-trial-20261012/RESULTS.md) and [saved-tangent diagnosis](ilvis0-rectangular-diagnosis-20261012/README.md) | Exposed sensitivity to starting near parameter limits; passing local linear problems did not establish observed convergence. |
| [Boundary-aware trial](ilvis0-boundary-recovery-trial-20261012/RESULTS.md) and [failure diagnosis](ilvis0-boundary-diagnosis-20261013/README.md) | Seventeen of 24 fits passed, but prediction-stability failures prevented complete stretch recovery. |
| [Fixed-endpoint probes](ilvis0-shared-leg-probes-20261014/README.md) and [precision comparison](ilvis0-shared-leg-precision-20261014/README.md) | Isolated arithmetic/derivative behavior in weak calibration directions before the successful precision recovery. |
| [First damped-solver qualification](ilvis0-trust-qualification-20261014/README.md), [diagnosis](ilvis0-trust-diagnosis-20261015/README.md) and [revised qualification](ilvis0-trust-v2-qualification-20261015/RESULTS.md) | Rejected a candidate that failed known optima, then qualified its revised step strategy on 48 controls. |
| [Saved stability audit](ilvis0-final-stability-audit-20261015/INTERPRETATION.md) and [native timing probes](ilvis0-timing-derivative-v2-20261016/README.md) | Found a timing-boundary discrepancy: a smooth predicted improvement could worsen the actual integrated result. |
| [Packet-aware solver trial](ilvis0-timing-trial-20261016/README.md) | Both controls passed, but its target primary and repeat still failed the original stability gate. |
| [All-six stopping audit](ilvis0-stopping-audit-20261016/INTERPRETATION.md) | Found timing-boundary behavior in every unfinished primary and reproduced an old-gate rejection at a known cusp minimum. |
| [Two-sided rule](ilvis0-boundary-stop-qualification-20261016/RESULTS.md), [adapter](ilvis0-boundary-adapter-qualification-20261016/RESULTS.md) and [compiled-motion checks](ilvis0-boundary-native-qualification-20261016/RESULTS.md) | Passed 43, 30 and two software controls respectively, qualifying a bounded diagnostic rather than changing old labels. |
| [All-six timing-boundary diagnostic](ilvis0-boundary-diagnostic-20261016/README.md) | Preserved eight completed checks before an interrupted journal blocked continuation; the interrupted identity remains unresolved. |
| [Interrupted-run accounting audit](ilvis0-accounting-audit-20261016/README.md) and [receipt controls](ilvis0-receipt-qualification-20261016/RESULTS.md) | Verified eight saved checks and qualified durable per-charge accounting without repairing the incomplete original journal. |
| [Unstarted-check continuation](ilvis0-boundary-continuation-20261016/README.md) | Completed the twelve previously unstarted identities in 233 native calls, preserving the interrupted identity and earlier checks. |

| [Complete timing-boundary review](ilvis0-boundary-review-20261016/README.md) | Verified companions, controls and repeat agreement; added one globe preference, bringing the total at that stage to **48 globe / 0 flat / 5 unresolved**. |

| [Adjacent-boundary trial](ilvis0-boundary-followup-20261016/RESULTS.md) and [complete review](ilvis0-neighbor-review-20261017/README.md) | Explicitly checked a neighboring timing boundary; both controls and the target pair passed in 44 calls, adding a globe preference: **49 globe / 0 flat / 4 unresolved**. |
| [Clustered-boundary diagnostic](ilvis0-clustered-boundary-20261017/README.md) and [complete review](ilvis0-cluster-review-20261018/README.md) | Located a stable point among closely spaced timing boundaries; both controls, all six primaries and the required diagnostic repeat pass, adding one globe preference: **50 globe / 0 flat / 3 unresolved**. |
| [Remaining timing profile](ilvis0-remaining-time-profile-20261018/README.md) | All ten checks passed: both starts agree at each fixed offset under both processing assumptions; free-time completion remains untested by this diagnostic. |
| [Matched free-time test](ilvis0-remaining-free-time-v2-20261018/RESULTS.md) | Both controls passed, but all four target fits failed the full stopping gate despite close repeat agreement; the tally stays unchanged. |
| [Remaining-endpoint audit](ilvis0-remaining-free-time-audit-20261018/README.md) | Separates timing-only stationarity failure from fresh-correction failure and places the endpoints near integration boundaries, using saved data without refitting. |
| [Matched two-case boundary diagnostic](ilvis0-remaining-boundary-20261018/RESULTS.md) | Both controls and the profiled-removal pair passed; both unsubtracted endpoints stopped at the probe-spacing guard. The tally stays unchanged. |
| [Narrow-boundary clock audit](ilvis0-narrow-boundary-audit-v2-20261018/README.md) | Verified distinct, correct clock states below the fixed spacing guard, motivating a separately qualified numerical check; no native calls or model fits. |
| [Representable timing probes](ilvis0-representable-boundary-20261018/README.md) | All 31 software checks and all four observed checks passed; 56 native evaluations verified the two blocked endpoints and fresh controls with unchanged scientific stopping limits. |
| [Complete two-case review](ilvis0-representable-review-20261018/README.md) | Verified all six primary fits and both required repeat pairs from saved evidence, adding one globe preference: **51 globe / 0 flat / 2 unresolved**. |
| [Final two-stretch audit](ilvis0-final-two-audit-20261018/README.md) | Separated geometry guards, unchecked neighbors and unstable calibration corrections in nine saved outcomes; no new integrations or fits. |
| [Focused nearby timing pair](ilvis0-final-pair-boundary-20261018/README.md) | Both controls passed; both targets stopped before evaluation because of a saved-context representation error. |
| [Corrected receiver context](ilvis0-final-pair-boundary-v2-20261018/README.md) | Completed 54 native calls without software errors; both controls passed, but both targets failed the fresh right-side correction despite close repeat agreement. |
| [Saved correction systems](ilvis0-correction-audit-20261018/INTERPRETATION.md) | Reproduced a successful local-solver status with a worse affine objective than the feasible zero step, using six saved-system solves and no native predictions. |
| [Range-scaled affine correction](ilvis0-scaled-pair-boundary-20261018/README.md) | Passed 33 software checks and all four observed checks in 54 native evaluations, retaining all physical bounds and full native stopping limits. |
| [Complete scaled-correction review](ilvis0-scaled-pair-review-20261018/README.md) | Verified all six primaries and both processing-case repeat pairs, adding one globe preference: **52 globe / 0 flat / 1 unresolved**. |
| [Last-stretch field-endpoint checks](ilvis0-last-field-boundary-20261018/README.md) | All six checks passed in 100 native evaluations, including both processing-case pairs; the separate zero-field timing disagreement remains. |
| [Last-stretch zero-field timing profiles](ilvis0-last-time-profile-20261018/README.md) | All eight fixed-time fits and two controls passed in 132 evaluations; four repeat comparisons reproduced the two competing offsets. |
| [Last-stretch free-timing comparison](ilvis0-last-free-time-20261018/RESULTS.md) | Both controls passed; four repeatable target fits failed full stability in 190 evaluations, leaving the last stretch unresolved. |
| [Last-stretch saved correction audit](ilvis0-last-correction-audit-20261018/INTERPRETATION.md) | Isolated a large proposed timing move almost at a packet transition; fixed-time corrections are micrometre-scale, and affine scaling alone does not fix it. |
| [Last-stretch two-sided timing checks](ilvis0-last-zero-boundary-20261018/RESULTS.md) | All four zero-field endpoint checks and both fresh controls passed in 102 evaluations; both processing-case repeat pairs agreed. |
| [Final complete model review](ilvis0-last-review-20261018/README.md) | Verified six model/case primaries, four repeat pairs and two fresh controls, completing recovery at **53 globe / 0 flat / 0 unresolved**; preserved all 28 focused outcomes. |

## Supporting controls and earlier simulated-flight work

The [remaining timing/calibration comparison](ilvis0-timing-basins-20261017/INTERPRETATION.md)
examined eight outstanding endpoint pairs using saved data only. It distinguishes
widely separated timing solutions from nearby solutions with calibration-stability
failures, guiding the next matched profile without changing the published tally.

| Work | What it contributed |
|---|---|
| [Geographic](ilvis0-geographic-controls-20261011/README.md), [latitude](ilvis0-latitude-controls-20261011/README.md) and [course controls](ilvis0-course-controls-20261007/README.md) | Checked model geometry and demonstrated calibration ambiguity even when reconstructed tracks were very accurate. |
| [Longer-interval](ilvis0-interval-controls-20261011/README.md), [coupled-motion](ilvis0-coupled-controls-20261011/README.md) and [increment-correction controls](ilvis0-compensation-controls-20261011/README.md) | Tested how duration, aircraft motion and integration corrections affect recovery of known parameters. |
| [Correlated-error](ilvis0-error-model-controls-20261012/README.md), [training-only](ilvis0-error-training-controls-20261012/README.md) and [nonlinear uncertainty controls](ilvis0-nonlinear-uncertainty-controls-20261012/README.md) | Checked uncertainty calculations while identifying effects that remain uncalibrated for the archive. |
| [Native uncertainty adapter](ilvis0-native-uncertainty-controls-20261012/README.md) | Checked all 27 parameter columns on six software paths without treating them as observed-data confidence validation. |
| [Synthetic development pilot](development-1000-20261006/README.md) and [matched airline pilot](matched-airline-pilot-20261006/README.md) | Tested selection, nuisance effects and decision availability before archival data became the primary project. |
| [Extended airline pilot](extended-airline-pilot-20261006/README.md) and [observed-route replay](observed-pair-replay-20261007/README.md) | Added longer simulated checks and real route geometry; these remain development simulations, not measured IMU evidence. |
| [Wind](wind-tas-development-20261006/README.md), [magnetic ambiguity](magnetic-ambiguity-development-20261006/README.md) and [flight-domain checks](flight-domain-development-20261006/README.md) | Developed more realistic moving-aircraft nuisance and eligibility models for the former passenger-flight design. |

[What comes next](NEXT_STEPS.md) covers unfinished comparisons, measurement-channel
checks, reserved-observation prediction, freely estimating the rotation field and
the proposed solar-versus-sidereal rate test. The [ground experiment](STATIONARY.md)
is a separate consumer-IMU project under development.
