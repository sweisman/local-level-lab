# Studies and what each added

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
