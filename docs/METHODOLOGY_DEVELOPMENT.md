# How the airborne analysis has developed

Local Level Lab compares recorded aircraft motion under competing surface geometries.
An **IMU (inertial measurement unit)** measures turning and acceleration; a GPS receiver
records the aircraft's route. This page explains how the analysis was built and checked.
The [methodology](METHODOLOGY.md) explains the measurement principle, and the
[findings](ilvis0-highspeed-segments-20261008/FINDINGS.md) document the selected tracks
and results.

## 1. Establish the observations and freeze the selection

NASA's ILVIS0 recordings supported airborne lidar surveys. The analysis preserves
the original IMU increments and reconstructs positions from the primary receiver's
recorded output. The combined IMU/GPS navigation solution is used for decoder checks
and motion screening, not as fitted evidence. Receiver coordinates still use geodetic
conventions; separate recorded streams do not make the comparison free of coordinate
assumptions. The [archive guide](ILVIS0.md) describes decoding and provenance.

All 232 retained recordings were screened before model comparison. Eligibility requires
at least four continuous minutes, every supported receiver speed reading at least
700 km/h, and the frozen motion, timing and completeness rules. This produced 53
stretches totaling 424.3 minutes. The [selection record](ilvis0-highspeed-segments-20261008/ELIGIBILITY.md)
preserves exact intervals, source hashes, speeds and exclusions.

Each complete stretch is fitted jointly under three candidates: globe with a specified
background rotation field, globe with zero background field, and the specified stationary
flat disc. Two processing cases allow either no upstream field removal or a shared amount
removed onboard. Both allow constant gyro offsets of ±1 degree/hour. That is a sensitivity
assumption, not a measured drift specification.

Shape is evaluated first, comparing the disc with the better globe fit. A background-field
comparison is reported only after all required fits finish and both processing cases
favor globe. Shorter residual sections are consistency checks, not additional flights.

## 2. Complete the first comparison and audit its coverage

| Whole-stretch result | Count |
|---|---:|
| Globe preferred under both processing cases | 12 |
| Specified flat disc preferred | 0 |
| Required numerical fits unfinished | 41 |

The twelve completed comparisons also favor the specified background field over zero.
These are substantial empirical preferences. Unfinished calculations do not give the
models equal support, and successful numerical completion does not mean equal fit quality.
Some recordings overlap or share instruments; these are not automatically twelve
independent replications. Statistical significance has not yet been calibrated.

Completed recovery extends these first-pass results and includes IMU8 recordings.
The [generated current status](CURRENT_STATUS.md) gives the combined totals and
background-field comparisons. The original table above is historical;
[updated findings and source tracks](ilvis0-position-stability-trial-20261013/FINDINGS.md)
show the additional evidence and its recording overlap.

The earlier [six-recording pilot](ilvis0-refinement-20261008/PROVISIONAL.md) found two
complete globe preferences under its four tested cases, two partial globe-favoring
comparisons, and two recordings without complete shape comparisons. It remains a
separate preserved study.

The [post-run review](ilvis0-highspeed-segments-20261008/POST_RUN_REVIEW.md) found that
most unfinished fits exhausted their numerical allowance. The
[calibration and fit-quality audit](ilvis0-calibration-audit-20261010/README.md)
compared the same twelve resolved stretches under both processing cases: median
horizontal mismatch was 0.068 m for the background-field globe, 29.5 m for the zero-field
globe and 47.1 m for the disc, using each candidate's declared coordinate metric.
These are errors against observations used for fitting, not independent predictions.
The audit also found frequent calibration parameters at their permitted limits.

## 3. Separate integration timing from calibration readjustment

The [epoch-level diagnostic](ilvis0-residual-diagnostic-20261010/README.md) reproduced
individual saved track errors on two recordings without refitting. Replacing nominal
200 Hz intervals with elapsed packet-header time at the same parameters increased
vertical error from roughly 0.6–0.7 m to 9.2–9.4 m. A timestamp need not describe exactly
the integration interval represented by an increment.

The subsequent [matched clock comparison](ilvis0-clock-trial-20261010/README.md)
refitted all three models under both processing cases on the completed control.
All six fits converged and retained the globe and background-field preference;
calibration readjustment restored vertical error to about 0.70 m. The
[clock/calibration audit](ilvis0-clock-calibration-audit-20261011/README.md) showed gravity
correction moving away from its limit while Z-axis gyro gain and offset stayed at theirs.
This demonstrates sensitivity and readjustment, not independent proof of the correct clock.

A separate [within-interval integration comparison](ilvis0-integration-audit-20261011/README.md)
finished four of six fits and retained the Z-axis limits. It did not qualify a replacement
for the original method.

## 4. Check whether extreme Z-axis corrections create the preference

The [twelve-fit calibration comparison](ilvis0-calibration-trial-20261011/README.md)
finished eleven fits. Fixing Z gain to zero preserved globe and background-field
preferences under both processing cases. Fixing Z offset to zero left one required
fit unfinished, so that comparison remained unresolved.

The next tests fixed gain and offset together across a small grid, allowing all other
parameters their original bounds:

| Calibration check | Completed fits | Result |
|---|---:|---|
| [October 5 joint grid](ilvis0-z-profile-audit-20261011/README.md) | 27/27 | Every grid point favored globe, then the specified background field. |
| [Same grid with possible upstream field removal](ilvis0-z-profile-removal-20261011/RESULTS.md) | 27/27 | Preferences persisted. |
| [Preselected September 24 recording](ilvis0-z-profile-replication-20261011/RESULTS.md) | 25/27 | Seven complete comparisons favored globe; two remained unfinished. |

The grid spans Z gyro gain −2%, zero and +2%, and constant offset −1, zero and
+1 degree/hour. On the first recording, background-field horizontal errors remained
0.081–0.093 m, versus 29.0–29.6 m for zero-field globe and 63.6–64.1 m for the disc.
The preferred fits needed at most one remaining parameter at its limit. The advantage
therefore did not require the original extreme Z corrections. These tests do not
identify the instrument's true calibration and are repeated checks, not new flights.

The [saved follow-up audit](ilvis0-z-followup-audit-20261012/README.md) compares all 81
fits and preserves the two unfinished labels despite their small errors and passing
saved stationarity checks. The profiled removal fraction on the first recording stayed
essentially zero. The second recording's full-grid background-field conclusion remains withheld.

## 5. Examine uncertainty and predictions beyond fitted observations

Small errors alone do not establish reliable uncertainty. The
[residual correlation audit](ilvis0-residual-covariance-20261012/README.md) found slow
vertical correlation on October 5, including errors a minute apart, with less slow
correlation on September 24. The original uncertainty adjustment did not remove all
dependence. A shared correlated-error alternative is development work, not a calibrated
replacement likelihood.

[Software uncertainty controls](ilvis0-nonlinear-uncertainty-controls-20261012/README.md)
check correlated errors, training-only estimation, nonlinear behavior and calibration
limits. [Native integration controls](ilvis0-native-uncertainty-controls-20261012/README.md)
check all 27 calibration and processing derivatives against independently constructed
paths. These validate calculations rather than certify observational uncertainty.

The [retrospective prediction trial](ilvis0-prediction-trial-20261011/README.md) finished
five of six fits. The later [training/prediction covariance comparison](ilvis0-prediction-covariance-20261012/RESULTS.md)
finished ten of twelve; its combined comparison remains unresolved. Predictions on
reserved times are more informative than fitting those times, but these development
tests do not constitute independent-flight confirmation.

## 6. Qualify numerical recovery before extending it to the unfinished stretches

A solver is the numerical procedure that searches for the best permitted fit. Its
completion checks assess both proximity to an optimum and whether another feasible
step materially changes the result. A failed check is not evidence for either geometry.

| Numerical check | Outcome |
|---|---|
| [Initial matched solver trial](ilvis0-solver-trial-20261010/README.md) | 10/12 completed versus 11/12 previously; no rollout. |
| [Known-answer software qualification](ilvis0-solver-qualification-20261010/README.md) | 34/34 predefined starts passed; no additional flight evidence. |
| [Saved-point continuation trial](ilvis0-convergence-recovery-trial-20261012/README.md) | 15/24 passed; eight unfinished primary fits recovered, but none of three test stretches fully resolved. |
| [Alternative-method software screen](ilvis0-recovery-diagnosis-20261012/METHOD_SCREEN.md) | Rectangular method passed 30/30 controls; the previous method passed 29/30 in that saved environment. |
| [Separate rectangular-method archival trial](ilvis0-rectangular-recovery-trial-20261012/RESULTS.md) | 8/24 passed: all six completed controls, two unfinished primary fits and no perturbed repeats. No test stretch became fully resolved; qualification failed. |
| [Boundary-aware nonlinear controls](ilvis0-boundary-controls-20261012/README.md) | Bounded linear steps passed 40/40 known-answer checks, versus 35/40 for the original method and 38/40 with a snapped start. No archival fits. |
| [Boundary-aware archival trial](ilvis0-boundary-recovery-trial-20261012/RESULTS.md) | Complete: 17/24 passed, including nine unfinished primaries, all six controls and two repeats. No test stretch became fully resolved; qualification failed. |
| [Saved boundary-trial diagnosis](ilvis0-boundary-diagnosis-20261013/README.md) | Six failures pass stationarity but fail prediction stability; one exhausts its budget. All three primary/repeat pairs have nearly identical costs and tracks but opposite stopping outcomes. No new native predictions or fits. |
| [Actual-position stability comparison](ilvis0-position-stability-trial-20261013/README.md) | Fresh full-model position checks preserve gradient and objective limits. The archival trial passed 24/24 fits, all controls and all repeats; three previously unresolved stretches favor globe. |
| [Remaining-stretch recovery](ilvis0-position-recovery-20261013/README.md) | Completed: 159 new starts, 117 passing fits, all six controls passed. Eighteen original unfinished stretches now pass their full comparison and scheduled repeat; combined tally 30 globe, zero flat, 23 unresolved. Physical assumptions unchanged; no retries. |

| [Paired wider-arithmetic qualification](ilvis0-paired-precision-trial-20261014/RESULTS.md) | 16/16 fits passed in 129 sweeps, including both controls and repeats. Two additional stretches resolve, bringing the tally to 32/0/21. Physical assumptions and numerical stopping tolerances unchanged. |

| [Completed cost-only precision recovery](ilvis0-cost-precision-recovery-20261014/RESULTS.md) | 83/86 fits passed in 891 sweeps and about four hours. Both controls and all twelve repeats passed; nine more stretches have complete comparisons. Tally at that stage: 41 globe, zero flat, 12 unresolved. Three primary fits exhausted their small evaluation allowance; all prior failures remain preserved. |

Software controls have known answers and expose numerical failures without choosing
favorable flight data. Their success cannot guarantee success on the archive. The
completed trial retains the original physical models and bounds, preserves old results,
and allowed no retries. It did not qualify a full rerun of the 41 unfinished stretches.

The [saved-tangent audit](ilvis0-rectangular-diagnosis-20261012/README.md) distinguishes
ten early gradient failures, three early stability failures and three exhausted fits.
A known-answer control reproduces a stall caused by starting one floating-point step
inside a parameter bound. Moving such coordinates to their exact limits improves
local affine-system completion from 12/24 to 16/24, but does not resolve every failure.
These are numerical diagnostics, not recovered flight results.

The separate boundary-aware candidate checks each bounded linear step against the
actual nonlinear cost and shortens rejected moves. It passes the predetermined
nonlinear controls, including weak and redundant directions. Its final stationarity
and fresh stability requirements are unchanged. Its completed observed comparison
does not qualify for wider use. Saved results now locate the remaining problem in
prediction-stability checks near nearly identical tracks, plus one genuinely
nonstationary budget failure. The separate actual-position rule checks the full
model's change in predicted receiver coordinates rather than allowing a local
residual estimate alone to reject it. Covariance unwhitening is verified against
direct native coordinates on independent short controls. Its 1 mm RMS / 1 cm maximum
limits describe numerical stability; they do not establish instrument accuracy or
calibrated uncertainty. A new finite observed trial is required before wider use.

## 7. Next milestone and interpretation

The priority is recovering more complete comparisons: qualify a representative subset,
check repeatability under a finite budget, then prepare a separately authorized
all-stretch recovery. The [roadmap](ANALYSIS_ROADMAP.md) also tracks absolute fit adequacy,
covariance calibration, receiver-coordinate and measurement-channel controls, and
independent prediction. Exact device identification continues at lower priority.

A later [rotation-field study](ROTATION_FIELD.md) will estimate the retained field's
direction and magnitude freely. The present fixed-rate comparisons neither identify
its ultimate cause nor distinguish solar from sidereal rate. Geometry, a measured
field and its causal explanation remain separate questions. Explanations predicting
identical observations cannot be distinguished by these recordings alone.
