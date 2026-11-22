# Archived analysis roadmap

This page preserves the earlier research record. Statements about what comes next reflect those study stages. See the [current page](ANALYSIS_ROADMAP.md) for the active status and plan.

# Analysis roadmap

## Where the project stands

<!-- current-status:start -->
**53 with the specified-field globe preferred, 0 flat-disc preferences, 0 without a consistent preference** among 53 selected stretches.
See the [verified current status](CURRENT_STATUS.md) for coverage, background-field comparisons and the numerical checks recorded for each cohort.
<!-- current-status:end -->

Both solvers agreed on all 16 matched pairs on one ESA development
window. At nearby starting points that fit equally well, their forecasts
differed by less than 0.27 mm. [Solver comparison](mixed-tangent-hybrid/OBSERVED_DISPATCH_FRESH_RESULT.md)

On that window's 400 later positions, four of 16 primary forecasts met the
fixed accuracy limits. All four used the specified field and the policy that
allowed persistent receiver errors. The check used one development flight and
two globe models. [Held-out forecast accuracy](mixed-tangent-hybrid/ESA_DISPATCH_ACCURACY_RESULT.md)

An earlier GPS error correction improved later height in all seven
additional NASA groups tested. The same correction increased height
error in all six cases on the ESA development flight.
[NASA check](prediction-group-transfer/HEIGHT_TRANSFER_RESULT.md) ·
[ESA check](prediction-observed-development/ESA_HEIGHT_ERROR_TRANSFER_RESULT.md)

Nine of twelve unadjusted ESA forecasts met the fixed accuracy limits.
An adjustment learned from earlier GPS positions brought all three
available rolling misses inside the limits. At one cut, only 25 of the
first 120 later GPS heights fell inside the nominal 95% range.
[Raw accuracy](prediction-observed-development/ESA_RAW_ACCURACY_RESULT.md) ·
[Adjusted comparison](prediction-observed-development/ESA_MATCHED_CONDITIONING_RESULT.md) ·
[Uncertainty](prediction-observed-development/ESA_MATCHED_UNCERTAINTY_RESULT.md)

The [height-role check](prediction-observed-development/ESA_HEIGHT_ROLE_RESULT.md)
shows that the 800-cut adjustment improved height without bringing
most positions inside the stated bands. The separate 400-cut model
ranking survives when only north and east are scored.

The [structured scoring check](prediction-observed-development/ESA_STRUCTURED_AXIS_SCORE_RESULT.md)
reproduced all 80 path scores and kept operator storage linear in the
number of later observations. This makes longer comparisons practical.
The aircraft error model still needs qualification.

The [raw receiver preflight](prediction-observed-development/ESA_RINEX_WINDOW_RESULT.md)
matched all 520 times in the ESA 400/120 comparison. The raw measurements,
orbit and clock files are available. Two [GPS code reconstructions](prediction-observed-development/ESA_RINEX_CODE_RESULT.md)
solved all 1,041 epochs. Both [preserved the forecast ranking](prediction-observed-development/ESA_RINEX_CODE_COMPARISON_RESULT.md)
on the 120 later reports. The comparison checks GPS processing sensitivity
on one flight. The airborne prediction error law remains unqualified.

The [final satellite-product check](prediction-observed-development/ESA_PRECISE_GPS_SUPPORT_RESULT.md)
supports an orbit-only comparison with every original GPS satellite.
The clock product omits G17, so a clock comparison needs the same
reduced set on both sides. The airport base record remains unverified.
The [completed orbit-only replay](prediction-observed-development/ESA_FINAL_ORBIT_REPLAY_RESULT.md)
shifted the later GPS positions by 0.90 m RMS and preserved the ranking
and preferred-model accuracy result in both complete settings.
The [matched clock replay](prediction-observed-development/ESA_RELATIVE_CLOCK_REPLAY_RESULT.md)
changed those positions by 0.42 m RMS and preserved both rankings at the
same satellite set. This leaves constant clock offsets and other common
receiver errors open.
In a [matched-field replay](prediction-observed-development/ESA_SHAPE_RECEIVER_REPLAY_RESULT.md),
all eight receiver paths favored globe after allowing smooth motion
corrections. The score came closest to a tie with GPS L1 code only.
The working covariance does not account for the much larger errors of
the code-only paths. A bound for the observed ranking has to address the
1.07-unit distance from a tie on that path as well as the 25.41-unit
separation between the fixed predictions.
The [receiver-margin calculation](prediction-observed-development/ESA_SHAPE_RECEIVER_MARGIN_RESULT.md)
shows that a worst-case change of 4.43 cm per coordinate could reverse
the score for the original export. A smoother four-block error needs a
much larger path change. Qualifying an aircraft error model requires
both the size and timing of receiver errors.
The [processed receiver check](prediction-observed-development/ESA_PPP_SHAPE_ERROR_RESULT.md)
finds changes of only about 0.03 score units on the same model comparison
and a maximum relative change of 0.38 units on 188 fast windows.
The same-antenna evidence leaves common error open.
The [carrier-phase replay](prediction-observed-development/ESA_CARRIER_PHASE_LATER_RESULT.md)
recovers the later aircraft motion within 12.3 cm RMS after a single
earlier position anchor. It shifts the fixed shape score by −0.208 and
leaves the globe preferred. The earlier clock break stays excluded.
The [whole-window replay](prediction-observed-development/ESA_CARRIER_PHASE_CONTINUOUS_RESULT.md)
then accounts for the clock step and starts at the first earlier position.
Its shape score differs from the later-only replay by less than 0.001.
The [single-satellite check](prediction-observed-development/ESA_CARRIER_SATELLITE_INFLUENCE_RESULT.md)
leaves the carrier score between −7.79 and −6.60, with a tie at zero.
Position-like errors shared across satellites remain open. The [ground
reference search](prediction-observed-development/ESA_GROUND_REFERENCE_AVAILABILITY.md)
found no same-day entries for the nearby stations in the public indexes checked.
The [carrier-error calculation](prediction-observed-development/ESA_PHASE_ERROR_SCORE_RESULT.md)
shows that 3.01 cm per observation could bring the fixed score to a tie if
the range errors align in the worst possible pattern. Under independent
errors, one score standard deviation reaches the same margin at 39.7 cm
per observation. The aircraft error pattern remains unmeasured.
The [raw receiver comparison](prediction-observed-development/ESA_PARALLEL_RAW_RECEIVER_RESULT.md)
matched three receivers on 518 one-second intervals. In the later window,
the two alternate receivers agree to 1.77 mm RMS in carrier-range change.
Both differ from AIR1 by about 5–6 mm RMS. The common-antenna check can now
test receiver-specific effects on the score.
The [relative score check](prediction-observed-development/ESA_RAW_RECEIVER_SCORE_RESULT.md)
used those differences to shift the existing AIR1 path. The fixed score
moved from −7.13 to −7.07 and −7.28. Shared receiver errors remain open.
The [Galileo-only replay](prediction-observed-development/ESA_GALILEO_PHASE_PATH_RESULT.md)
also preserves the shape preference on both receivers, with scores of
−7.08 and −7.19. The two later Galileo paths agree to 1.94 cm RMS in 3D.
The [withheld accuracy replay](prediction-observed-development/ESA_RECEIVER_ACCURACY_REPLAY_RESULT.md)
applied the unchanged position limits on twelve receiver paths. The
specified-field globe forecast ranked first and passed in all 24
comparisons. Shared receiver error and coverage on other flights remain open.
The [earlier-only atmospheric delay fit](prediction-observed-development/ESA_CARRIER_DELAY_FIT_RESULT.md)
moves the later GPS carrier path by 0.29 m RMS. Both position checks still pass
and the fixed shape comparison keeps its result. The later carrier residual
improves by only 0.45%, leaving the source of the error uncertain.
The [separate GLONASS path](prediction-observed-development/ESA_GLONASS_PHASE_PATH_RESULT.md)
agrees with GPS to 7.0 cm horizontal RMS and differs by 97.3 cm
height RMS in the later window. Both preserve the fixed shape score's
preference. The shared antenna and working atmosphere leave common
error open.
The [same-day sounding check](prediction-observed-development/ESA_SOUNDING_DELAY_RESULT.md)
sets up two measured alternatives to the working atmosphere. Over the
later two minutes the modeled overhead delay increases by 1.7–6.3 cm at
reported height, with less than a centimetre of change from the last
training report in either scenario. The [matched carrier replay](prediction-observed-development/ESA_SOUNDING_CARRIER_RESULT.md)
then measures up to 6.7 cm horizontal and 15.5 cm height RMS shifts. All
four saved trajectories keep the same fixed shape preference. The numerical
paths were audited separately from a preserved result-record failure.

Both [GLONASS code reconstructions](prediction-observed-development/ESA_GLONASS_COMPARISON_RESULT.md)
also preserved the ranking, using different satellites and the same
aircraft antenna. The original forecasts and 120 later times were unchanged.

The [direct Doppler check](prediction-observed-development/ESA_DOPPLER_COMPARISON_RESULT.md)
recovered all 1,041 velocities with each constellation. Integrated motion
agrees with the receiver export within 0.30 m horizontal RMS and 0.27 m
height RMS over the 120-second forecast window.

The [Doppler force comparison](prediction-observed-development/ESA_DOPPLER_FORCE_RESULT.md)
finds that changing receiver velocity sources affects the predicted
force more than switching between globe and disc under the same field.
This accelerometer-only check leaves shape unresolved.

The [gyro direction check](prediction-observed-development/ESA_GYRO_FORCE_DIRECTION_RESULT.md)
uses the same force averages. With the specified field retained in
the gyro, the globe follows the measured direction changes within
0.002–0.011° RMS. The trial does not bound gyro calibration or
unknown onboard corrections.

The [matched-field gyro check](prediction-observed-development/ESA_MATCHED_GYRO_DIRECTION_RESULT.md)
gives both shapes the same specified background field. Allowing each
shape any retained gyro fraction still leaves a globe advantage of at
least 0.062° RMS on this cut. Gyro gain and bias remain open.

The [calibration replay](prediction-observed-development/ESA_GYRO_DIRECTION_CALIBRATION_RESULT.md)
finds that the working X-axis accelerometer bias can reverse the
directional ranking. The earlier position fit still needs to test
whether that explicit correction is compatible with the flight.

The [earlier position replay](prediction-observed-development/ESA_X_BIAS_POSITION_REPLAY_RESULT.md)
found that all six checked endpoint points exceed the original loss
allowance. The exact affine certificate quantifies the nonlinear
compensation that would still be needed. A full nonlinear exclusion
remains open.

The [ground bias check](prediction-observed-development/ESA_GROUND_X_BIAS_RESULT.md)
finds more within-stop force variation at that endpoint than under
smaller bias corrections. Ground motion and measurement error still
need independent limits before this can exclude the endpoint.

The [continuous X-bias check](prediction-observed-development/ESA_X_BIAS_DIRECTION_PROFILE_RESULT.md)
keeps the direction comparison in favor of globe through +0.0225 m/s²
with other sensor terms fixed. The ground data fit almost equally
well at that boundary, leaving the full positive range open.

The [earlier affine position bound](prediction-observed-development/ESA_X_BIAS_RANGE_POSITION_RESULT.md)
puts X bias below +0.0040 m/s² for the specified-field globe.
The still-globe and stationary-disc fits use larger corrections.
The nonlinear gap remains open.

The [exact boundary search](prediction-observed-development/ESA_X_BIAS_NONLINEAR_RANGE_RESULT.md)
reduced the earlier horizontal error to 7.72 m RMS. Its weighted
loss still exceeded the original allowance. It provides a checked
point and leaves the full nonlinear range open.

The [shared GPS error check](prediction-observed-development/ESA_SHARED_RECEIVER_ERROR_RESULT.md)
found that the path would have to move by 3.22 km RMS for the disc to tie
or beat both fixed globe forecasts. The position-accuracy screen could
fail with a 3.93 m RMS path change concentrated at one report.

The training constraints narrowed all eleven remaining calibration ranges.
Keeping those constraints together then brought the upper bound on score
movement to 53.04 units, compared with a 25.41-unit globe–disc forecast gap.
Four disc ranges still have upper bounds larger than the gap. The zero-field
comparison remains unresolved over the full calibration range.
[Earlier residual projection](prediction-observed-development/ESA_LINKED_FULL_LOSS_RESULT.md)
could set aside at most 0.067% of the squared-loss budget and left the
53.04-unit bound effectively unchanged.
[Joint calibration check](prediction-observed-development/ESA_LINKED_JOINT_SCORE_RESULT.md)
Testing the earlier loss constraint directly at 44 score thresholds left
that bound unchanged. [Score threshold check](prediction-observed-development/ESA_LINKED_SCORE_FLOOR_RESULT.md)
The [proposal reconstruction](prediction-observed-development/ESA_LINKED_FLOOR_WITNESS_RESULT.md)
found two relaxed disc proposals above the gap. Both missed an affine
constraint. Their earlier losses rose far above the allowance when the
terms were tied to one calibration.
The [linked range check](prediction-observed-development/ESA_LINKED_FLOOR_SUPPORT_RESULT.md)
used those earlier residuals across the full physical boxes. Splitting
tightened 17 of 20 certificates without lowering the combined score bound.

The [gyro-free rate check](ilvis0-measurement-contribution/SHARED_GPS_MOTION_RATE_RESULT.md)
still leaves all four cases overlapping after applying the saved 27 cm
GPS correction. Comparing them directly needs independent limits on
aircraft motion and a receiver error model.
[The catalog check](ilvis0-measurement-contribution/MOTION_SOURCE_AUDIT.md)
found no overlapping timed LVIS images. NCAR lists a one-second aircraft
file for one stretch, useful to pursue separately as motion context.

## Current milestones and finish line

This sequence takes priority over the older development backlog below.

| Milestone | Work and exit gate |
|---|---|
| 1. Evidence and public wording | Recount the original and later NASA cohorts from their ledgers. State the model set, offset cap, sample concentration, selection history and recorded repeat coverage. Separate raw and conditioned forecasts and show both failed and passing generated gates. |
| 2. Shared controls | Independently qualify the globe/disc and zero/specified-field comparison, including both processing cases. Test a gyro-free comparison with shared calibration and explicit attitude ambiguity, a ±1/3/10/20°/h gyro-offset grid, and consistent receiver-coordinate and covariance changes. Preserve physical inadequacy, numerical failures and unidentifiability as separate outcomes. |
| 3. Bounded NASA pilot | Freeze a metadata-selected subset across distinct groups, courses, latitudes and both IMU types where feasible. Match numerical allowances and acceptance checks across models. Report whether the differences persist with the same field and wider gyro offsets. Expand only if comparisons are repeatable and adequate and the remaining stretches can answer a stated open question. |
| 4. Aircraft errors and ESA development | Qualify uncertainty and absolute withheld accuracy, then evaluate the three selected windows from ESA recording 187 under matched conditions. Keep both IMU error laws and prioritize persistent bias, drift, calibration and correlated receiver error. |
| 5. Independent confirmation and reproducibility | The [flight-group decision software](FLIGHT_GROUP_DECISION.md) checks both stages and retains missing results. Before opening the seven protected ESA groups, qualify and freeze the selection, within-group error model, adequacy rule and decision limits. Publish dependency-closed evidence. The isolated NASA training and forecast replays are recorded below. |

The work closes with verified evidence for each milestone and a clear record
of unresolved scientific questions. A failed gate can close its own study;
dependent claims remain unqualified. Free field estimation, solar versus
sidereal precision and consumer expansion remain follow-on work.

The [flight-group calibration audit](prediction-observed-development/GROUP_RANK_RESOLUTION_RESULT.md)
verifies that the existing twelve generated histories cannot give small
enough p-values for a rank-based decision. The software now counts failed
reference draws and retains every declared error scenario. Before booking
a larger run, justify the aircraft error scenarios and check its required
reference resolution and likely ability to separate the models.
The [single-model reference option](PREDICTION_GROUP_DECISION.md#a-cheaper-reference-test)
passes software checks and could cut reference fits from three to one per
setting. It still needs a qualified aircraft error law and a power check.

### Execution order and completion checks

1. **Package the completed whole-period simulation.** The v3 study has a
   verified [portable replay](prediction-simultaneous-law-family-v3/REPLAY.md).
   It restores 251 frozen sources and reproduces all 96 outcomes, including
   95 successes, from the original and continuation evidence. Extraction
   and exact report replay have been checked without the shared catalog.
   The [isolated NASA refit](ilvis0-matched-trial-observed-runtime/refit-evidence/README.md)
   also reproduced the training fit and native builds exactly under the
   pinned toolchain. The run reached its wall limit before forecasting. A
   [separate one-call replay](ilvis0-matched-trial-observed-runtime/forecast-evidence/README.md)
   used the saved fit and reproduced all 223 later positions exactly.
2. **Advance the shared controls while packaging proceeds.** Wire the local
   matched-field and gyro-free controls into the full fitting and prediction
   pipeline. Qualify on independently generated cases before preparing the
   NASA pilot. Continue NASA and ESA work only through the gates in the
   milestone table. Keep the earlier solver diagnostics as evidence for
   specific failures that affect those gates.
3. **Proceed through each verified gate.** After a study closes, verify the
   outcomes, update the public roadmap, study index and relevant overview,
   and start the next ready task. Use a finite, reboot-resumable allowance
   for each new study. Preserve failed gates and their charges. Continue
   independent work when a gate blocks dependent fits. Any follow-up must
   address a specific diagnosed failure and have a distinct, justified test.
4. **Close with an evidence and backlog audit.** Verify the covered claims
   from a clean checkout. For each milestone, record its result, any
   abstention and which downstream claims remain unavailable. Stage external
   publication as reviewable, dependency-closed batches. Follow repository
   authorization rules for Git and external publication while other ready
   work continues.

The initial NASA fit set was fixed for its own run after earlier archive
exploration. The original pass completed 12 comparisons, and later numerical
studies completed 41 under several stage-specific policies. No new study
inherits a fit allowance or a numerical pass from those stages. The
[current status](CURRENT_STATUS.md) supersedes totals printed in the
[first-pass](ilvis0-highspeed-segments-20261008/FINDINGS.md),
[stability](ilvis0-position-stability-trial-20261013/ANALYTICS.md) and
[cost-precision](ilvis0-cost-precision-recovery-20261014/README.md) reports,
which are preserved as historical evidence.

The [v2 whole-period simulation](prediction-simultaneous-law-family-v2/RESULT.md)
failed its 5% gate with four timeouts and a 9.28% upper failure bound. The
[separate v3 cohort](prediction-simultaneous-law-family-v3/RESULT.md) passed
with 95/96 recordings and a 4.85% upper bound for its generated mixture.
Aircraft coverage remains unqualified. This gate is separate from the
4,344-fit validation and the study that used the 4.2 threshold.

The first [matched-field software controls](../analysis/tests/test_ilvis0_matched_field.py)
check local specific force and angular rate against independent generated
globe and disc trajectories. They also exercise exact constant-offset
profiling for fixed body motion and show that different gyro-free attitude
histories can attain the same force error at one shared calibration. The
linear receiver coordinate check preserves propagated force variance when
both covariance and derivative weights are transformed. The midpoint
propagator matches the three existing candidates under both tested removal
settings and reconstructs a known stationary disc-with-field state at three
removal fractions. A continuous reference check also reproduces generated
moving globe and disc histories at fractional packet times.

The [matched native training checks](../analysis/tests/test_ilvis0_matched_training.py)
exercise all four candidates in both removal cases. They compare native
values with the reference, check the new disc derivative independently,
charge each fit and forecast call, and verify that continuing past the
training cut reproduces the fitted prefix. The gyro-free path retains the
same receiver windows and projects their covariance jointly across all four
candidates. A separate control fits one accelerometer and gravity
calibration across the chosen history, with explicit free attitude twists.
These short software checks exercise the data flow and arithmetic. The
[frozen generated comparison](ilvis0-measurement-contribution/MATCHED_GENERATED_RESULT.md)
then exercised the complete offset grid. All 128 fits passed the technical
checks, and all 32 truth-matched fits passed stopping and withheld accuracy.
Only 12 of 32 settings have a numerical stop for every candidate. The
remaining comparisons stay unresolved. The [fixed-point arithmetic replay](ilvis0-measurement-contribution/MATCHED_PRECISION_RESULT.md)
reproduced all 33 original endpoint and probe costs. Wider arithmetic
brought 31 cost changes below the unchanged limit at the same points.
Two exceeded the limit, including one probe that substantially raised cost.
The [prospective wider calculation](ilvis0-measurement-contribution/MATCHED_WIDE_RESULT.md)
then passed the generated-data gate. It completed all four candidates in
15 of 16 matched settings, versus six with binary64, preserving all six
previously complete settings. All 16 truth-matched wider fits passed the
withheld accuracy check. One wider comparison remains unfinished.
The [receiver-window uncertainty control](ilvis0-measurement-contribution/SUPPORT_POLICY.md#first-known-answer-results)
keeps every possible selection after a bounded position error. It
reproduced known motion for all four candidates and retained their shared
receiver uncertainty when the allowable window changed. A [shared-calibration
check](ilvis0-measurement-contribution/SUPPORT_POLICY.md#shared-accelerometer-calibration)
now retains the known model on all eight moving controls with unknown
orientation. The [shared GPS height-error check](ilvis0-measurement-contribution/SHARED_GPS_ERROR_RESULT.md)
found no reversal of the same-field globe–disc force difference across
919 saved windows for the tested error. The [raw GPS coverage preflight](ilvis0-measurement-contribution/GPS_RECONSTRUCTION_PREFLIGHT_RESULT.md)
then found L1 satellite range and orbit support for all 48,099 selected
epochs across the 21 streams. The [two-flight GPS position comparison](ilvis0-measurement-contribution/GPS_RECONSTRUCTION_PILOT_RESULT.md)
then solved all 2,224 planned cases. Height-processing differences
produced 0.017–0.099 m/s² vertical acceleration disagreement in
10-second windows and 0.0016–0.0087 m/s² in 30-second windows. The
[same-window force comparison](ilvis0-measurement-contribution/GPS_FORCE_COMPARISON_RESULT.md)
found no sign change in the same-field shape difference in 3,213
windows. GPS height processing changed individual forces more than the
shape difference. The [observed input layout](ilvis0-measurement-contribution/MATCHED_OBSERVED_PREFLIGHT_PLAN.md)
now binds both recordings to the original inertial source hashes and
finds 1,111 exact common epochs with separate training and scoring cuts.
The [original-packet preflight](ilvis0-measurement-contribution/MATCHED_OBSERVED_INPUTS_RESULT.md)
then passed both clocks with the full timing allowance. The [eight-case recorded
preflight](ilvis0-measurement-contribution/MATCHED_OBSERVED_NUMERICAL_RESULT.md)
now has six verified stopping and forecast passes. The IMU8 zero-field disc
fit failed its stop at 30 evaluations. The IMU21 zero-field disc case did
not start before the wall limit. Both four-candidate comparisons remain open.
The [IMU21 continuation](ilvis0-measurement-contribution/MATCHED_UNSTARTED_DISC_RECOVERY_RESULT.md)
passes the original stop and completes the four forecast slots on that
recording. Globe has lower horizontal and 3D error at both matched fields.
Disc has lower height error at zero field. The [shared GPS reference check](ilvis0-measurement-contribution/MATCHED_IMU21_RECEIVER_HULL_RESULT.md)
preserves both results at four horizons. At zero field, the full 3D
ordering needs 84.39 m of additional per-report displacement allowance
to reach a tie. The IMU8 stopping failure stays
sealed. A [saved trace check](ilvis0-measurement-contribution/MATCHED_REPEATED_TRIAL_RESULT.md)
finds seven duplicate proposals among its 30 evaluations. The opt-in solver
passed the [eight generated full-fit checks](ilvis0-measurement-contribution/MATCHED_REUSE_GENERATED_RESULT.md)
with 15% fewer training evaluations and identical stopping outcomes, costs
and later positions. The [recorded-aircraft qualification](ilvis0-measurement-contribution/MATCHED_REUSE_OBSERVED_RESULT.md)
reproduced both converged controls exactly, with no duplicate proposal
on either flight.
The [GPS extension](ilvis0-measurement-contribution/GPS_RECONSTRUCTION_EXTENSION_RESULT.md)
verified both position solutions at all 1,124 epochs from two further
preselected flight groups. The [packet check](ilvis0-measurement-contribution/MATCHED_EXTENSION_INPUTS_RESULT.md)
matched all 1,123 original reports to both reconstructions and verified
support on both clocks. The [matched forecast plan](ilvis0-measurement-contribution/MATCHED_EXTENSION_FORECAST_PLAN.md)
uses the 375 kept-back reports to compare the four candidates on these groups.
The [four-group audit plan](ilvis0-measurement-contribution/MATCHED_FOUR_GROUP_AUDIT_PLAN.md)
applies the same fixed accuracy limits to the earlier and added flights,
with a separate row for each conservative flight group.
The [eight added fits](ilvis0-measurement-contribution/MATCHED_EXTENSION_FORECAST_RESULT.md)
all pass. The [four-group audit](ilvis0-measurement-contribution/MATCHED_FOUR_GROUP_AUDIT_RESULT.md)
verifies 15 of 16 forecasts. Globe gives lower 3D error at the specified
field on all four flights, and at zero field on all three complete pairs.
The specified-field globe meets the fixed accuracy screen on three flights.
On the two added flights, the [shared GPS check](ilvis0-measurement-contribution/MATCHED_EXTENSION_RECEIVER_HULL_RESULT.md)
preserves both accuracy passes and the 3D rankings across the measured spread.
The [added force-only check](ilvis0-measurement-contribution/MATCHED_EXTENSION_FORCE_RESULT.md)
leaves the shape decision open. IMU21 clears the necessary inequality for
all four candidates. IMU8 still has small force gaps for three candidates
after a gain chosen from earlier data, including both globe candidates.
One [shared receiver correction](ilvis0-measurement-contribution/MATCHED_EXTENSION_FORCE_WITNESS_RESULT.md)
clears all 79 gaps with a largest move of 1.02 m and preserves every
full-IMU forecast rank. The gyro-free comparison still leaves shape open.
The [gain-range check](ilvis0-measurement-contribution/FORCE_GAIN_RANGE_RESULT.md)
also clears every later one-sided check within the gains allowed by the
earlier data, without moving GPS. The remaining predicted force gaps require
an independent error budget before they can help decide shape.
The [paired check on the same windows](ilvis0-measurement-contribution/PAIRED_FORCE_WINDOW_RESULT.md)
finds a small mixed-recorder discrepancy at the logged clock which a ±5 ms
clock allowance leaves unresolved. Whole-packet bounds are too wide to
establish the accuracy targets, especially for the two IMU21 streams.
The [gyro-free calibration controls](ilvis0-measurement-contribution/GYRO_FREE_CALIBRATION_CONTROLS_RESULT.md)
pass all eight generated training and later-force comparisons. The
packet-motion bound requires a supported limit on within-packet force changes.
The [adjacent-packet check](ilvis0-measurement-contribution/PACKET_FORCE_CHANGE_RESULT.md)
rules out force-change limits below about 260 and 273 m/s³ on the two
added flights when the extra error allowance is 0.1 m/s² per axis.
An upper limit supported by motion and instrument evidence remains open.
The seven reserved ESA groups remain closed pending aircraft-error qualification.
The [receiver-spread check](ilvis0-measurement-contribution/MATCHED_FORECAST_RECEIVER_RESULT.md)
then retained the same-field globe forecast advantage even when the common
reference could vary between all three GPS solutions at every epoch. The
smallest full-forecast horizontal errors were 19.19 m and 2.03 m. Absolute
aircraft prediction adequacy remains open.
A [force-window split audit](ilvis0-measurement-contribution/SUPPORT_POLICY.md#keeping-training-and-later-force-windows-separate)
also finds 680 training and 311 later 30-second windows with every GPS fix
on the correct side of the cut. Exclude the 60 crossing windows from a
held-out gyro-free comparison, with the remaining overlap accounted for
within each side.
The [common packet support check](ilvis0-measurement-contribution/MATCHED_FORCE_SUPPORT_RESULT.md)
then retained whole accelerometer packets in every one of those 991 windows
under both clocks and the full offset allowance. The IMU8 count interval is
comparable to the zero-field shape gap. IMU21's is much smaller. The
[matched force averages](ilvis0-measurement-contribution/MATCHED_FORCE_AVERAGE_RESULT.md)
preserve both same-field shape signs across all 5,946 window, clock and GPS
choices. A [training-only gain check](ilvis0-measurement-contribution/MATCHED_FORCE_GAIN_RESULT.md)
clears all training lower bounds with corrections below 1%. All four IMU21
candidates clear later checks. All four have some IMU8 violations. This
establishes how this scalar constraint responds to calibration. The
[shared receiver covariance check](ilvis0-measurement-contribution/MATCHED_FORCE_COVARIANCE_RESULT.md)
then projected an assumed GPS law over the same intervals. GPS error mostly
cancels in shape differences, while every later onboard lower-bound excess
was below one projected standard deviation. Joint calibration and real-aircraft
error qualification remain open.
The [shared receiver-error example](ilvis0-measurement-contribution/SHARED_FORCE_WITNESS_RESULT.md)
clears all 16 onboard IMU8 force-only gaps with one correction that moves
no receiver position more than 0.272 m. All four candidates and both clocks
use those same GPS positions. IMU21 cleared the original inequalities
without a correction. This advances the force-only comparison and leaves
the actual receiver-error law and independent aircraft motion limits open.
Applying the [same GPS correction to six saved IMU forecasts](ilvis0-measurement-contribution/SHARED_FORCE_FORECAST_RESULT.md)
changed every paired error gap by less than 0.2% and preserved all rankings.
This bounds the effect of a concrete shared receiver change at fixed fits.
The [pilot metadata audit](ilvis0-measurement-contribution/MATCHED_PILOT_ELIGIBILITY.md)
finds 21 stretches in 18 flight groups that meet the saved conversion and
receiver checks. All are southern, and all 19 IMU21 stretches are in the
southbound course sector. Freeze a pilot within that coverage if its gates
pass. The [northern decoder timing check](ilvis0-measurement-contribution/NORTHERN_IMU21_CLOCK_RESULT.md)
cleared two engineering failures under nominal timing. The original
two-date failure remained, so no northern stretch gained eligibility.
The [southern metadata reservation](ilvis0-measurement-contribution/MATCHED_PILOT_CANDIDATES_RESULT.md)
fixes four candidate groups with both IMU types, both available course
sectors and the widest eligible IMU21 latitude spread. It leaves fitting
gated on the separate qualification and execution freeze.
The [frozen cost cross-check](analysis-provenance/NASA_ZERO_FIELD_BY_GROUP.md#the-reserved-development-pilot)
finds that the two preflight stretches favored disc at zero field in the
original fits, while the two other reserved stretches favored globe.
The missing zero-field disc forecasts make the preflight comparison incomplete.

## Previous prediction development

The [twenty-group retrospective forecast extension](prediction-group-transfer/REMAINING_GROUPS_PREDICTION_RESULT.md)
sealed all 80 planned fits. Thirty passed their numerical stopping checks;
50 did not. Nine of the 20 groups have scored later-position forecasts within
the fixed earlier development reference and pass a separate physical screen.
Eleven groups lack a usable later-cut score. This tests one specified
globe-plus-field forecast on additional recordings from the same archive. It
does not compare Earth shapes, establish prediction coverage or provide
independent confirmation. The numerical failures remain part of the result.
The [fixed accuracy audit](prediction-group-transfer/ACCURACY_MARGIN_RESULT.md)
checks all 80 transfer forecasts and all 24 optimizer-comparison forecasts.
Each meets the original position-error screen, including 67 without a
numerical stop. This isolates the role of the numerical gate in the nine
accepted later-cut results. The smallest later-cut accuracy margin in the
transfer study is 5.57 m under arbitrary bounded GPS perturbations.
The [saved stopping audit](prediction-group-transfer/REMAINING_GROUPS_STOPPING_AUDIT.md)
finds that 49 failed the frozen fresh cost-change check, five of those also
failed fresh stationarity, and one failed initial stationarity. None exhausted
the evaluation allowance or failed the actual-position limits. The original
50 failed fit labels remain unchanged. The
[next solver qualification](prediction-group-transfer/NEXT_SOLVER_QUALIFICATION.md)
requires independent known-answer controls before any revised observed fit.
The [saved correction reconstruction](prediction-group-transfer/REMAINING_GROUPS_CORRECTION_DIAGNOSTIC.md)
matches every failed probe's recorded local prediction with no native calls.
For 31/49 candidates the local cost change lies below the old limit although
the fresh native change exceeds it. A [three-case forecast sensitivity check](prediction-group-transfer/CORRECTION_FORECAST_RESULT.md)
then found corrected-versus-original later-path changes from 0.038 mm to
16.3 mm. The first attempt stopped before native calculation because a C
source was omitted from its freeze; a separately qualified repair completed
all three calls. This is a numerical diagnostic on selected cases, not a
revision of the 50 failed fit labels or a forecast-accuracy test.
The [saved later-error audit](prediction-group-transfer/REMAINING_ERROR_STRUCTURE.md)
keeps all 20 groups in view and describes the nine scored forecasts. Their
median later-position RMS is 1.04 m north, 0.69 m east and 4.43 m in height.
Adjacent errors are nearly perfectly correlated, consistent with smoothly
varying forecast paths; they cannot serve as independent error draws.
This audit does not calibrate aircraft prediction coverage.
The [earlier-to-later correction check](prediction-group-transfer/ERROR_TRANSFER_RESULT.md)
reduced height RMS in 15 of 20 groups, including four of the five with
passing starts at both cuts. Horizontal RMS improved in only three
groups and crossed the fixed accuracy limit in one. The [height-only check](prediction-group-transfer/HEIGHT_TRANSFER_RESULT.md)
then reduced height RMS on seven additional groups, including all three
with passing starts at both cuts. Horizontal scores stayed identical.
Independent-flight validation of the error law remains open.
The [new generated solver forecast control](prediction-group-transfer/GENERATED_SOLVER_FORECAST_RESULT.md)
passes its frozen four-fit agreement gate in all six independently generated
model/clock fixtures. All 24 fits stopped, and the greatest cross-solver or
cross-start later-path spread was 2.44×10⁻⁷ m. These are 12-second,
six-parameter software controls; full-calibration and noisy long-record
controls remain necessary before any observed stopping-rule change.
The [four-fit pilot](prediction-group-transfer/FULL_CALIBRATION_SOLVER_RESULT.md)
tested all 26 calibration directions on one noisy generated history.
Both bounded solvers and both starts passed numerical
stopping and the generated physical screen on the same 60-second history.
Their largest later-path separation was 3.42×10⁻⁷ m. The forecast's
horizontal and height RMS errors against known later truth were about
0.32 m and 1.31 m. This is a one-history development check; more models,
clocks and noisy histories are needed before changing any aircraft fit.
The [multimodel full-calibration control](prediction-group-transfer/MULTIMODEL_SOLVER_RESULT.md)
then closed 24/24 fits across all three physical models and both interior and
near-boundary Z-gyro calibrations. All six four-fit forecast-agreement gates
and all 24 generated physical screens passed; the greatest later-path spread
was 9.17×10⁻⁷ m. The six fixtures share a declared noise seed. The
[nominal 200 Hz control](prediction-group-transfer/NOMINAL_200HZ_SOLVER_RESULT.md)
then passed all 24 fits and all six agreement gates with distinct noise seeds;
its largest later-path spread was 1.3×10⁻⁵ m. Exact-grid timing cannot test
irregular packet timestamps. The [longer generated confirmation](prediction-group-transfer/LONG_HORIZON_SOLVER_RESULT.md)
then passed all 24 fits and six preregistered gates over 120-second histories,
with 79 earlier and 40 withheld receiver reports. Its largest within-case
later-path spread was 5.06×10⁻⁵ m. The [saved aircraft two-start audit](prediction-group-transfer/REMAINING_PAIR_AGREEMENT.md)
found all 40 pairs within 0.1 m; the largest difference was 6.03 mm, even
though only 30/80 original fits passed their strict stopping checks. This
supports a separately frozen observed forecast-stability development method.
It does not retroactively pass the 50 failed fits or establish aircraft
prediction accuracy, coverage or an Earth-model decision.
The [solver-independence correction](prediction-group-transfer/SOLVER_INDEPENDENCE_ERRATUM.md)
limits what these generated passes establish: `near_zero` calls the same
`trust_v2` optimizer and changes its stopping logic. The comparisons used
two starts, but did not qualify an independent numerical method. A separate
bounded optimizer must pass generated controls before an observed
forecast-stability method is frozen.
The [short independent-method control](prediction-group-transfer/INDEPENDENT_SOLVER_RESULT.md)
now passes that distinct-optimizer check on six 60-second generated fixtures:
24/24 final stopping checks, six of six cost/path agreement gates, and 24/24
separate generated physical screens. Its largest within-case later-path
spread was 5.06×10⁻⁵ m. The 50 original failures stay fixed.
The [120-second comparison](prediction-group-transfer/LONG_INDEPENDENT_SOLVER_PLAN.md)
has now [passed](prediction-group-transfer/LONG_INDEPENDENT_SOLVER_RESULT.md):
24/24 fits met their stopping checks and all six generated histories met the
predeclared cost/path agreement gates. A host interruption left two charged
starts unfinished and two tasks unstarted; a separately qualified finite
recovery completed only those four identities. The original 20 completed
fits were not repeated. The versioned observed development pilot's
[one-fit SciPy real-worker preflight](prediction-group-transfer/OBSERVED_METHOD_V2_PREFLIGHT.md)
has now passed its technical wiring check; its 30-call fit did not converge.
The [24-fit matched recorded-data comparison](prediction-group-transfer/OBSERVED_METHOD_PILOT_V2_RESULT.md)
has closed under its own 200-evaluation-per-fit limits. All 24 fits completed
technically, but only 7 passed the numerical stopping checks and only four of
six matched recording/cut sets met the development path-agreement scale. The
observed method is therefore not qualified for a broader aircraft comparison.
The [saved-result diagnosis](prediction-group-transfer/OBSERVED_METHOD_V2_DIAGNOSIS.md)
finds that all 15 fresh-probe failures exceed the cost-change limit, although
only five also fail stationarity and three also fail a position-change limit.
Two inner cuts have materially different later paths despite similar training
costs. The [fixed-endpoint timing check](prediction-group-transfer/OBSERVED_FIXED_ENDPOINT_RESULT.md)
replays all eight selected points exactly and finds close timing derivatives
across the tested steps. One differing path pair has nearly the same fitted
time offset; the other does not. Next: assess the joint calibration valley and
later-path sensitivity. A changed stopping rule requires fresh independent
qualification; no original aircraft fit is reclassified.
The [24-vector calibration-swap check](prediction-group-transfer/OBSERVED_CALIBRATION_SWAP_RESULT.md)
finds that isolated parameter-group changes greatly worsen training fit even
though the two complete solutions have near-equal costs. The later-path
differences involve compensating calibration changes. Next: test the complete
connection between the saved solutions at fixed points; do not treat the
poor-fit hybrids as viable forecasts.
The [six-point complete-vector check](prediction-group-transfer/OBSERVED_PAIR_PATH_RESULT.md)
has now closed. The 2010 pair rises by 0.001835 in weighted training cost
at its midpoint above the worse endpoint; the 2015 pair stays within the
endpoint cost range. Both have later-path variation. The straight line does
not establish whether a curved low-cost connection exists. Next: qualify a
numerical method and stopping rule on independent generated controls before
another recorded-data comparison.

For long recordings, a [separate receiver-covariance calculation](prediction-observed-development/STRUCTURED_RECEIVER_LIKELIHOOD_RESULT.md)
matches the dense reference on small controls and processed 64,080 generated
receiver reports with 26 calibration directions in 23.49 seconds and 353 MiB
peak memory using the existing shared state-space core. This is a software and scale check. An observed short-prefix
comparison and an aircraft error-law qualification remain open. Six additional
checks now show that the earlier dense receiver law translates exactly to the
structured calculation under both zero and nonzero correlation time. A
[120-epoch observed training-prefix check](prediction-observed-development/STRUCTURED_RECEIVER_LIKELIHOOD_RESULT.md)
also matches dense and structured whitening at the actual coordinate scale;
its 26 design columns are software probes. A [one-call native follow-up](prediction-observed-development/STRUCTURED_RECEIVER_NATIVE_RESULT.md)
then matches all 26 real calibration derivatives at one fixed point to
1.43×10⁻¹¹ maximum whitened difference. The
[matched short-prefix fits](prediction-observed-development/STRUCTURED_RECEIVER_FIT_RESULT.md)
then both passed stopping after 61 evaluations and produced nearly identical
training paths under the same law. This qualifies the computational switch
on that prefix; aircraft error-law adequacy and long-recording prediction
remain open.

An **IMU (inertial measurement unit)** contains gyroscopes that measure turning
and accelerometers that measure specific force. The analysis combines those
records with receiver positions to reconstruct the aircraft's motion.

The 53 stretches favor globe geometry and the model with a specified background
rotation signal. These are completed model comparisons. Statistical confidence,
prediction accuracy and independence between recordings still need testing.

The [new 96-recording generated whole-period check](prediction-simultaneous-law-family-v3/RESULT.md)
passed its frozen 5% recording-level gate: 95 recordings passed both fits and
contained every later coordinate of both targets; one recording failed its
numerical checks and counts against the gate. The exact one-sided 95% upper
failure bound is 4.85% for the declared generated mixture. Its qualified
continuation finished the 92 tasks left after an interrupted launch without
repeating sealed work. The [previous cohort](prediction-simultaneous-law-family-v2/RESULT.md)
failed the same gate because four tasks hit its time limit. Neither cohort
establishes error coverage for observed aircraft. The
[saved generated fitted-error audit](prediction-simultaneous-law-family-v3/FITTED_INNOVATIONS_RESULT.md)
finds far less persistent height error after fitting than the opened ESA
development recording, but its shorter and differently generated histories
cannot calibrate an aircraft error-law rejection. The next error-law gate is a
matched full-fit known-answer control. The
[local ESA tangent control](prediction-observed-development/LOCAL_PROJECTION_NULL_RESULT.md)
projects 2,048 white histories per law through the saved 26-direction fit;
zero reach the observed height correlation at either tested lag. This narrows
the diagnosis under the declared fixed covariance but does not qualify that
covariance or replace a nonlinear complete-fit control. The
[two-fit generated 600-report pilot](prediction-observed-development/FULL_FIT_INNOVATION_NULL_RESULT.md)
closed both numerical fits but failed its physical accuracy gate: known-truth
training horizontal errors were 55.3 and 33.3 m, and later errors were 219.2
and 156.1 m. Its fitted height residuals are almost uncorrelated, unlike the
ESA development fit. This small failed pilot does not qualify an aircraft
error range. The
[saved generated-path audit](prediction-observed-development/GENERATED_PATH_ERROR_AUDIT_RESULT.md)
separates the under-0.4 m training receiver error from 33–55 m fitted-path
error, which grows sharply through training. Full-path uncertainty is the
next generated qualification target. The
[bound-aware technical pilot](prediction-observed-development/BOUND_AWARE_GENERATED_PILOT_V2_RESULT.md)
kept all 26 directions and closed 2/2 fresh generated tasks; both truths lie
inside the affine intervals, but both raw paths still fail the [coded physical
screen](prediction-observed-development/GENERATED_ACCURACY_RULE_ERRATUM.md).
Nonlinear coverage, physical adequacy and the observed error law
remain separate open gates. A
[saved whole-forecast calculation](prediction-observed-development/GENERATED_SIMULTANEOUS_BOUND_RESULT.md)
then widens each of the 900 future coordinates for nominal 95% joint coverage
under the generated affine Gaussian assumptions. Both known paths remain
inside; their point fits still fail physical accuracy. Nonlinear and observed
aircraft coverage remain unqualified. A
[saved calibration-direction audit](prediction-observed-development/GENERATED_WEAK_DIRECTION_RESULT.md)
finds one almost identical weak combination of gyro gain, gravity adjustment
and vertical acceleration bias in both fits. It identifies a nonlinear stress
target without establishing the cause of either path miss. A
[finite native follow-up](prediction-observed-development/GENERATED_WEAK_DIRECTION_NONLINEAR_RESULT.md)
then shows that a fixed 0.20-unit move changes the later path by less than
0.7 m under both generated laws, with about 0.013 m tangent remainder. It
does not explain the 91–109 m original miss or qualify real-aircraft
uncertainty. The
[saved range-width audit](prediction-observed-development/GENERATED_BOUND_COMPONENTS_RESULT.md)
attributes about 71–81% of the median marginal half-width to calibration
uncertainty under the assumed generated law. It does not explain the point
path error or qualify an aircraft error law. The
[known-calibration audit](prediction-observed-development/GENERATED_CALIBRATION_RECOVERY_RESULT.md)
finds 0.47 and 0.35 half-range RMS differences from the two generated true
sensor settings. Three fitted sensor parameters reach limits despite
interior truth. The two-case check does not identify the path-miss cause. The
[known-calibration substitution](prediction-observed-development/GENERATED_CALIBRATION_SUBSTITUTION_RESULT.md)
then worsens both native paths when the other fitted coordinates stay fixed,
showing strong parameter coupling rather than a one-coordinate repair. The
[eight-case generated cohort](prediction-observed-development/GENERATED_BOUNDED_COHORT_RESULT.md)
then closes all fits, but none passes the coded physical path screen. Broad
assumed intervals contain all eight known futures on the same route. The
following [saved noise-floor audit](prediction-observed-development/GENERATED_NOISE_FLOOR_AUDIT_RESULT.md)
finds that the cohort's declared fixed-calibration noise alone implies a
17.39 m horizontal error scale over the later period, compared with the
inherited 0.1 m clean-data screen. This calls for a separately frozen
noise-aware physical adequacy rule, not relabeling the original failures.
The aircraft error law remains unqualified. The
[next generated qualification](prediction-observed-development/NOISE_AWARE_ADEQUACY_PLAN.md)
will first check a noise-aware forecast metric and usefulness rule in
software, with separate true-position and receiver-measurement targets, then
freeze independent generated confirmation. The [first six-case software
control](prediction-observed-development/FORECAST_ENVELOPE_CONTROL.md) now
passes; the [dual-target generated pilot](prediction-observed-development/DUAL_TARGET_GENERATED_RESULT.md)
has now closed 2/2 full technical tasks and 2/2 converged fits. Both target
ranges were saved before later data, but the receiver ranges are broad and
independent empirical coverage remains. The
[finite matched-candidate matrix](prediction-observed-development/MATCHED_CANDIDATE_GENERATED_RESULT.md)
closed 12/12 recordings and 36/36 converged fits after its
[technical preflight](prediction-observed-development/MATCHED_CANDIDATE_PREFLIGHT_RESULT.md).
Every later receiver path falls inside all three candidate ranges; no pair
separates. The [saved horizon and width audits](prediction-observed-development/MATCHED_CANDIDATE_GENERATED_RESULT.md)
find that separation stays below range width; by the final withheld position,
the calibration component is about 98.4% as large as the generated horizontal half-width.
A [saved calibration-identifiability check](prediction-observed-development/MATCHED_CANDIDATE_GENERATED_RESULT.md)
finds Z-axis gyro bias and vertical accelerometer bias among the largest
components of the weakest training direction in all twelve correct-model
fits. A separately frozen geometry control is next. The
[saved opened-ESA comparison](prediction-observed-development/ESA_SAVED_WEAK_DIRECTION_RESULT.md)
also finds Z-axis gyro bias dominant in the weakest training direction of all
20 converged candidate fits from one development flight; four other fits
remain nonconverged. This supports testing geometry, not treating the fits as
independent replications. A [saved duration check](prediction-observed-development/ESA_TRAINING_DURATION_WEAKNESS_RESULT.md)
shows that extending that flight's earlier training data from 400 to 600
receiver reports raises the weakest local singular value 2.35-fold and the
conditional Z gyro-bias Jacobian-column norm 3.23-fold. The longer forecast still
misses later heights, so this does not qualify the aircraft error law. A
[four-case generated geometry control](prediction-observed-development/GEOMETRY_CALIBRATION_CONTROL_RESULT.md)
finds higher local sensitivity on a turning path, but both turning fits fail
their stopping checks and remain unresolved. Its shallow climb is too small to
isolate the larger climb in the opened ESA flight. The
[saved ESA error-pattern audit](prediction-observed-development/INNOVATION_MORPHOLOGY_RESULT.md)
finds a strong low-frequency height component and documents all 120 lag
values; it does not identify its physical cause or supply a calibrated law.
The [training receiver-quality check](prediction-observed-development/TRAINING_QUALITY_AUDIT_RESULT.md)
finds that apparent PDOP/satellite associations reverse after time adjustment,
so it does not assign the height error to the receiver.
The
[full-size ESA development preflight](prediction-observed-law-preflight/RESULT.md)
passes four no-fit error-operator constructions on the real recording. The
[completed development continuation](prediction-observed-development/CONTINUATION_RESULT.md)
then scored 400 later receiver positions without refitting: both forecasts
miss the preset horizontal accuracy limits, so the next gate is physical
prediction adequacy. A [saved-rate audit](prediction-observed-development/RATE_HYPOTHESIS_AUDIT.md)
reconstructs the 360,028 ESA increments exactly and compares three sampling
interpretations. Its small signed component differences cannot establish
trajectory sensitivity or the actual instrument convention. A fixed-parameter
native propagation comparison is the next finite diagnostic. Seven independent
ESA groups remain reserved.
Its [frozen question and work ceiling](prediction-observed-development/RATE_PROPAGATION_PLAN.md)
keep the saved fit and initialization fixed while changing only the constructed
rate increments. The three tasks must pass a generated control and recovery
qualification before observed execution.
The [first three-task attempt](prediction-observed-development/RATE_PROPAGATION_V1_RESULT.md)
completed but failed its strict baseline-reproduction gate by 0.0000145 m in
height. It used the ordinary tangent kernel; the original sealed forecast used
the extended-precision kernel. Its saved alternatives remain diagnostic data,
not a qualified rate comparison. A newly frozen matching-kernel run is next.
The [matching-kernel repetition](prediction-observed-development/RATE_PROPAGATION_V2_RESULT.md)
then passed all three technical tasks and reproduced the original forecast
exactly. Reassigning the reported ESA rates to the left or right sample changes
the later horizontal trajectory by 43.37 or 19.47 m RMS at the old fitted
point. None of the three conventions passes the observed prediction-accuracy
gate. The next development test must refit each convention on earlier data
only, then score later data without selecting a method from those later errors.
The [finite six-task plan](prediction-observed-development/RATE_REFIT_PLAN.md)
keeps both original IMU error laws and the same nuisance bounds for all three
rate interpretations. Generated controls and task recovery must qualify
before the observed run; the seven ESA confirmation groups stay reserved.
The [first generated control](prediction-observed-development/RATE_REFIT_V2_SMOKE_RESULT.md)
exposed a software-gate mistake: the original deliberately short generated
fits were nonconverged. A separate corrected six-task control now reproduces
all saved fits, forecasts and nonconverged statuses and passes its technical
gate. Source-bound tests and the unchanged observed convergence gate precede
the development refits.
The [completed observed refit](prediction-observed-development/RATE_REFIT_V2_RESULT.md)
passes all six numerical checks, yet every rate method and both error laws
miss the preset accuracy screen: training horizontal RMS is 37.69–39.96 m and
later RMS is 240.37–249.41 m. Rate assignment alone does not resolve the
development prediction error. The scientific decision remains abstain; saved
residual diagnosis of the shared error is next, with seven groups reserved.
That [saved residual diagnosis](prediction-observed-development/RATE_REFIT_COMMON_RESIDUAL.md)
is complete: 245.85 m later horizontal RMS is shared across rate methods,
versus 5.87 m RMS method spread. The common miss grows through the recording.
Its physical cause remains unknown, so the next gate is a separately qualified
initialization/calibration/force/receiver-error diagnosis, not a method choice
from withheld errors or an independent-flight confirmation claim.

## Next: test predictions on unused measurements

The [revised prediction protocol](PREDICTION_VALIDATION.md) separates a practical
prediction comparison from formal uncertainty certification. First qualify the
training-only fitting and prediction pipeline on known-answer controls. Then fit
earlier observations in a small, metadata-selected archival pilot and score
later positions without using them to adjust the answer.

Preserve the original physical bounds and compare all three candidates under
matched assumptions. Use predeclared starts, choose primaries by training cost
only, and report every failure. Show horizontal and height errors together.
Differences between repeated predictions are sensitivity evidence, not confidence
intervals. Actual error-law assessment and calibrated significance remain open.

The [completed prediction pilot](ilvis0-retrospective-prediction-pilot-v2/INTERPRETATION.md)
fully compares one recording across both clocks and both processing assumptions:
later horizontal RMS is 0.84–1.13 m for specified-field globe, about 496 m for
zero-field globe and 793 m for disc. Two other recordings retain numerical or
accuracy failures. Broader validation remains open. These are retrospective
development tests; reserved ESA groups stay protected.
The [saved receiver-only control](receiver-only-forecast-baseline/INTERPRETATION.md)
uses the same three withheld periods with no IMU input. Its constant-velocity
horizontal errors are 87–351 m. A [spherical-path receiver control](receiver-only-geodesic-control/INTERPRETATION.md)
reduces those errors to 33–189 m. On the northern complete comparison, the
IMU forecasts remain much closer than either fixed receiver-only rule. A
gyro-specific channel ablation and calibrated adequacy remain open.

The [saved receiver-precision comparison](receiver-precision-holdout/README.md)
matches every pilot epoch to the same receiver's precision report. Of 36
settings, 28 have a numerically qualified start chosen from earlier data only.
The specified-field globe passes the pilot's uncalibrated accuracy screen in
seven of its nine qualified settings, but even its median later errors are
about four times the receiver-reported horizontal precision and eleven times
the height precision. The receiver estimates are not a full prediction-error
budget; observed-aircraft adequacy and uncertainty calibration remain open.
Across the nine qualified specified-field globe settings, a straight time
trend explains a median 95.7–97.4% of centered later-error variation by axis.
This describes already observed errors; the slope was not known from training.
The [fixed training-only drift check](prediction-drift-control/README.md)
tests that missing step. Its straight-line correction worsens seven of nine
qualified specified-field globe forecasts and improves the alternatives,
which still miss by hundreds of metres. A deterministic residual line is not
a qualified replacement for the combined error model.
The [next error-law gate](PREDICTION_ERROR_LAW_PLAN.md) first tests
identification and later-error coverage on known-answer controls. Any adjustable
quantities must come from earlier observations; protected confirmation groups
remain closed until the method and flight groups are frozen.
A twelve-case short native aircraft matrix now completes fits and saves
separate physical-position and future-receiver uncertainty targets before
later truth. It covers three models, both processing cases and two synthetic
IMU input-error forms. The source-bound clock/calibration matrix and coverage
test are next.
A separate exact-period 200 Hz generated path now passes native training under
both declared clocks. A separate deterministic packet-time disturbance keeps
the generated IMU increments and receiver reports fixed; the two native
forecasts then differ. The actual archive clock is not established by this
software control.
The [24-case generated-aircraft uncertainty check](bounded-calibration-prediction/NONLINEAR_RESULT.md)
is complete. All 24 technical cases and withheld-position accuracy screens
pass; one fit fails its numerical stopping check, so the combined gate is
23/24. The bounded intervals contain every tested coordinate but are broad;
this development matrix does not establish calibrated nonlinear coverage.
The [saved diagnosis](bounded-calibration-prediction/NONLINEAR_DIAGNOSIS.md)
shows its proposed timing step crosses packet boundaries for all 79 training
queries. A short clean control finds negligible error across such a boundary,
so the long noisy case received a [finite targeted timing probe](bounded-calibration-prediction/TIMING_PROBE_RESULT.md).
Its sealed values show that timing-only changes follow the tangent; the
coupled calibration/timing direction remains unresolved, and the probe's
technical wrapper is terminal. The separate
[48-case independent-seed check](bounded-calibration-prediction/INDEPENDENT_SEEDS_RESULT.md)
now passes every numerical and withheld-position gate on two new noise draws
per condition. Its broad bounds contain every tested coordinate. It does not
calibrate 95% coverage or establish an observed-aircraft error claim.
The [saved ESA precision check](esa-prediction-error-scale/README.md) matches
all 22 available forecasts to the receiver's reported uncertainty and retains
the two original fit failures. Even the specified-field globe forecasts exceed
receiver precision by large factors. Receiver precision alone cannot serve as
the uncertainty of an IMU-based aircraft forecast; this check is descriptive,
not a calibrated detection.

Global interval certification is now a separate research track. Its earlier
bounds and counterexamples remain published, with unchanged failure labels and
width targets. The [completed training-bound study](ilvis0-dense-physical-bounds/INTERPRETATION.md)
preserved 348 reports, but none of its six cases qualified. No further bound
expansion precedes the revised prediction sequence.

[Revised method and safeguards](PREDICTION_VALIDATION.md) ·
[Error assumptions](PREDICTION_ERROR_ASSUMPTIONS.md) · [Study history](STUDIES.md).

## Current phase and finish line

**An earlier generated decision-threshold validation is complete.** Calibration
set a fixed error limit for that separate simulated decision test. This does
not qualify the newer whole-period prediction intervals described above.
A reboot interrupted the original validation after 3,750 saved fits; its
complete-cohort rule cannot be met. A separate, reboot-resumable continuation
completed the other 594 fits. The independently replayed
[combined audit](prediction-validation-continuation/README.md) verifies all
4,344 fits across 181 preselected simulated cases. No case exceeded the limit;
the one-sided 95% failure upper bound is 1.64%, below the declared 5% target.
This validates the procedure under its simulated conditions. Aircraft error
coverage and Earth-model significance require further evidence.
The next gate is to test physical adequacy and prediction on preselected,
independent aircraft groups, with the receiver-error assumptions fixed before
using protected confirmation recordings. The generated-data threshold does not
transfer to observed aircraft by itself.
The [48-case generated-aircraft integration matrix](prediction-aircraft-error-integration/RESULT.md)
passes every technical pipeline check. Its deliberately short fits yield no
numerically converged or physically passing predictions, so it supplies no
uncertainty-coverage qualification. A longer, independently seeded known-answer
study must qualify training-only error estimation and prediction coverage.
The candidate-law comparison helper now enforces identical earlier IMU and
receiver measurements and records numerical score rankings without making a
scientific selection. Its four local checks pass. A separately frozen longer
generated-aircraft study still has to fit both laws to each *same* recording,
then test convergence and withheld coverage.

A [receiver-only binary inventory](ilvis0-trimble-position-precision/recorded-inventory/README.md)
now has saved outcomes for all 53 selected recording files. Fifty-two contain
accepted, checksummed position-precision reports; one fails the strict receiver
decoder. Those reports are receiver estimates. Their real error and time
correlation must be checked before they inform an aircraft prediction threshold.
The [paired-receiver study](ilvis0-receiver-overlap/recorded-study/README.md)
then completes all eleven usable overlaps. It measures close, strongly
correlated differences, but shared GNSS error remains unknown. It therefore
does not qualify the aircraft prediction-error law.

The detailed record below explains the development steps and failed releases
that led to this run. Those results remain separate from the current validation.

### Earlier development and frozen outcomes

**The [coordinate-precision controls are complete](coordinate-precision-controls/INTERPRETATION.md).**
Compensation passes all six known-answer cases, compared with three for the
original arithmetic and four for the longitude-only alternative. The study
returns all 18 tasks in 7.13 seconds after 46 source-bound software checks.

The [full saved-point check](saved-point-coordinate-precision/INTERPRETATION.md)
now passes all 315 derivative comparisons and all four stopping probes under
the original limits. It finishes in 27.2 minutes using 650 evaluations, after
99 software checks. The earlier matched diagnostic isolated the timing issue;
compensated accumulation also resolves the weak gyro-column precision problem.
The original labels, thresholds, observations and numerical environment stay
fixed. [Optimizer qualification](compensated-optimizer-qualification/INTERPRETATION.md)
now passes all 48 development fits, all 24 paired-start comparisons and all four
original input/error replays. It finishes in 30.3 minutes after 93 software checks.
The [fresh calibration release](prediction-calibration-compensated/INTERPRETATION.md)
stopped under its frozen failure rule after 909 returned starts in 9.58 hours:
904 passed, two failed numerical cost stability and three stopped cooperatively.
All 906 completed forecasts passed the fixed position-error screens. No finite
uncertainty threshold was established, so validation for that release did not start.
Both campaigns and their unused allowances stay closed. A
[saved timing review](prediction-clock-boundary-review/README.md) verifies
that both failed points lie close to internal integration boundaries. Check
the [saved linear corrections](prediction-linear-timing-review/README.md): all
four replay, while both failures cross all 119 query boundaries and the two
successful controls cross none. Four [analytical controls](timing-kink-controls/README.md)
also show the original check can reject exact nonsmooth minima with correct
derivatives. The physical-model cause remains unproved. Check both timing branches
before a separately reviewed method revision. The [four-point diagnostic](saved-timing-boundary/INTERPRETATION.md)
now completes all 78 evaluations in 6.7 minutes. Every saved input, residual and
27-column Jacobian replays exactly; all 18 within-interval timing derivative
comparisons agree. Most full-step prediction error appears in the timing-only
movement, while timing and other calibration effects nearly cancel.
[Steps constrained to timing intervals](TIMING_CELL_STEP_PLAN.md) now pass
independent known-answer qualification. The [saved-matrix review](saved-timing-cell-proposals/INTERPRETATION.md)
now returns all 18 successful linear solves after 26 software checks. All
feasible sides and spacings agree on the failed cases' proposed boundary;
their predicted remaining improvements fall below the original cost limit.
[Physical evaluation](saved-timing-cell-native/INTERPRETATION.md) now passes
all 18 proposals under the original cost, stationarity and position-change
screens. The run uses 26 evaluations in 2.6 minutes after 103 software checks;
the largest actual position change is about 1.5 micrometres. The next gate is a
complete interval-aware optimizer qualified on independent known optima,
non-optima and repeated starts. No earlier result is relabeled. No new campaign starts
automatically. Generated-data coverage and actual flight-level confidence
remain separate gates.

The [timing-aware stopping method](TIMING_STOPPING_PLAN.md) retains the
existing fitting method and numerical limits. Its
[analytical qualification](timing-stopping-qualification/INTERPRETATION.md)
now passes all 32 fits, eight direct controls and eight start-comparison
groups, using 1,008 evaluations in 26 seconds after 161 software checks.
The [four-fit native phase finished without qualification](timing-optimizer-regression/INTERPRETATION.md).
All original inputs replay, but all four fail final cost stability despite
passing the declared forecast screens. The failed checks use distant cell
midpoints. An independent curved-minimum control reproduces that false-failure
mechanism and passes with nearest feasible anchors. The
[local timing qualification](timing-local-qualification/INTERPRETATION.md)
now passes 36 fits, eight controls and all nine starting-point comparisons in
27.5 seconds after 175 software checks. Projection alone failed sharp-corner
tests before freezing; this version uses cell midpoints clipped to the existing
local timing window. It retains every cell, nuisance coordinate and numerical
limit. The [new four-case native trial](timing-local-native-regression/INTERPRETATION.md)
passes all fits, both start comparisons and all original input replays in
10.7 minutes after 189 software checks. The [48-case matrix](timing-local-matrix/INTERPRETATION.md)
now passes all 48 fits, all 24 start comparisons and four original input replays
in 65.7 minutes after 203 software checks. This completes the declared optimizer
qualification. Next is a [separately budgeted calibration/validation release](TIMING_CALIBRATION_RELEASE_PLAN.md),
with new cohorts, a frozen method and a checked handoff. Neither closed campaign
resumes; earlier labels are preserved.
The [local-timing calibration](prediction-calibration-timing/INTERPRETATION.md)
stopped under its frozen failure rule after 348 returned starts in 6.82 hours:
344 passed numerical checks, two failed timing-cell stability and two stopped
cooperatively. All 346 completed forecasts met the position-error limits.
The independent audit establishes no calibration threshold; validation was not
launched. The [saved-baseline diagnosis](timing-linear-baseline-diagnosis/README.md)
now reproduces worsening linear proposals in both failed cases, while the
matched controls do not worsen. All four saved calculations and their charges
were checked; the result-schema rejection remains preserved. No native call or
fit was run. The [feasible-initialization revision](timing-linear-anchor-check/INTERPRETATION.md)
now passes all 24 independent convex controls and four matched saved-matrix
checks after 56 source-bound checks; 90 related software tests also pass.
The previous method fails ten of the 24 controls. The
[fresh complete-optimizer qualification](timing-feasible-optimizer-qualification/INTERPRETATION.md)
now passes all 36 known-answer fits, eight direct probes and nine starting-point
groups in 27.8 seconds after 148 software checks. The separately frozen
[six-case native regression](timing-feasible-native-regression/INTERPRETATION.md)
now passes all six fits, three start comparisons and six original-input replays
in 10.6 minutes after 338 pre-execution software checks. Its 238-source freeze
retains all columns, bounds and limits. A reporting-only metadata repair passes
339 checks without rerunning fits. The [matrix audit](timing-feasible-matrix/INTERPRETATION.md)
now accepts all 44 completed fits and 22 complete start pairs in 51.0 minutes.
Four charged starts were interrupted by a runtime reset and remain failures.
All 1,239 publication artifacts and 28 native assets verify; the archived report
replays identically. Full matrix qualification is unavailable from this run.
A [separate four-case follow-up](timing-matrix-completion/INTERPRETATION.md)
passes all four fits, both start pairs and the remaining original replay in
4.6 minutes after 364 software checks. The
[saved-only combined audit](timing-matrix-combined/README.md) now qualifies
all 48 computational cases, 24 start pairs and four original replays after
16 additional assembler checks. All 241 common execution sources and the
environment match; the interrupted study retains its original failed state.
The [latest calibration release](FEASIBLE_PREDICTION_STATUS.md) stopped after an
execution interruption, with 1,813 numerically passing fits and four interrupted
starts after 38.7 hours. All 253 sources and the numerical environment still
match. Both starts of one required setting are unavailable, so the remaining
5,359 starts are closed unused. No calibration threshold or validation follows
from this incomplete cohort. The [independent audit](prediction-calibration-feasible/INTERPRETATION.md)
confirms all 1,813 completed forecasts also pass the position-error checks.
All 42,064 publication artifact hashes verify and the archived report replays
identically. The [recovery checker](execution-recovery/README.md) passes its
61-check software suite. The [host-service lifecycle control](execution-host-service/README.md)
also passes normal submitter-exit survival. The [fresh release](HOST_PREDICTION_STATUS.md)
has completed all 7,176 fits, all passing, in 151.7 hours after 154 software
checks and independent freeze verification. Its saved-data audit and publication
replay passed, supplying a finite prediction-error threshold. Independent
validation saved 3,750 passing fits before a host reboot interrupted four
charged starts. That original run cannot claim coverage under its own frozen
complete-cohort rule. The separately qualified continuation and combined
validation described above subsequently completed all 4,344 prescribed fits;
these earlier regressions do not establish observed-aircraft coverage.
This release and its unused allowance remain closed.

Previously, **calibration stopped early; validation was not run.** The
[phase report](PREDICTION_PHASE_RESULTS.md) records 1,683 qualified fits, two
numerical failures and one interrupted start. The one permitted saved-results
review identifies the cost-stability check as the failed numerical gate.
That completed phase's finite scope was:

1. Finish the existing calibration run within its original 299-family,
   7,176-start, 120-hour allowance. Preserve early stopping and every failure.
2. Run the separate 181-family, 4,344-start validation phase only if calibration
   supplies a finite, closed and verified threshold under the same population.
   Preserve its 72-hour ceiling and predeclared acceptance rule.
3. If either phase fails, permit **one saved-results diagnosis in total**:
   at most 24 existing fit records, no new noise draws, optimizer starts or native
   calculations, one numerical thread and a ten-minute cooperative ceiling.
   This review explains the failure; it does not retune the method or retry it.
4. Audit hashes and accounting, publish the outcomes and CSV data, update the
   overview pages, and write a concise phase report with findings, limitations
   and a prioritized follow-on backlog. **Then stop for review.**

Phase completion means an accurately audited and published outcome, including
a failed or inconclusive outcome. Passing the scientific gates is not promised.
Reporting repairs may verify and describe existing evidence; they cannot change
measurements, thresholds, solver rules or the frozen execution allowances.

The original 53-stretch findings, protected ESA groups, four-thread total limit
and prohibition on terminating processes remain in force. New campaigns,
solver experiments, broader aircraft fitting, free-field precision work and
participant expansion require a subsequent reviewed phase.

The [subsequent diagnostic plan](PREDICTION_STOPPING_PLAN.md) is now complete:
32 software checks, four saved points and 646 residual-and-derivative evaluations,
with unchanged acceptance rules. The [small follow-up controls](TIMING_PRECISION_CONTROLS.md)
also finish: 13 software checks, two reporting checks, seven native cases and
zero new fits. The [matched follow-up](saved-point-timing-arithmetic/INTERPRETATION.md)
now explains the timing discrepancy at the saved points but leaves the precision
problem open at that stage. The coordinate-accumulation controls, complete
saved-point check and optimizer qualification now pass. Fresh calibration
in that earlier phase stopped on two cost-stability failures, so its independent
validation was never launched. A later, separate generated-data release passed
the combined validation described above. The active backlog follows.

## Dependency-ordered backlog

This table retains the broader roadmap. Items beyond the current phase remain
follow-on work rather than automatic continuation instructions.

For U02, the [reference-draw work bound](FLIGHT_GROUP_DECISION.md#when-additional-reference-draws-cannot-change-a-rejection)
can identify when unfinished draws cannot change a rejection at a fixed
cutoff. The software checks passed. Aircraft error calibration remains open.
The [cohort work check](FLIGHT_GROUP_DECISION.md#when-the-whole-cohort-can-stop)
extends that calculation to the final shape and field decisions. It passes
exhaustive small-cohort controls and keeps the frozen reference denominator.
The [matched forecast adapter](PREDICTION_GROUP_DECISION.md) now feeds the
rank calculation and the dependence-aware decision. Known-answer controls
pass, and all 12 saved generated cases correctly abstain at the illustrative
5% limit because they have too few references. The next gate is an error law
and reference population that apply to the target aircraft.
For the reproducibility milestone, the [ESA saved-table check](prediction-observed-development/ESA_RINEX_CODE_COMPARISON_RESULT.md#reproduce-the-comparison)
passed with only the report files. Rebuilding the forecast errors from
positions still requires the sealed parent studies.
The [ESA group evidence index](analysis-provenance/ESA_GROUP_EVIDENCE.md)
joins 14 scored cuts from one recording. It verifies 2,120 distinct later
receiver rows. Of those, 360 also occur in another cut's training interval.
Three selected cuts and seven reserved groups remain separate from the scores.

The E02 ground-control series now includes a [second receiver-selected stop
and raw IMU comparison](prediction-observed-development/SECOND_GROUND_IMU_RESULT.md).
The two mean-vector magnitudes are 16.37 and 13.27°/h. Within-stop motion and
unknown heading leave the aircraft error law and a free background-field
estimate unqualified. Independent ESA groups remain reserved.
A [1/10/60-second audit](prediction-observed-development/GROUND_RATE_SCALE_RESULT.md)
also confirms that logged-rate variation changes sharply with averaging time.
It is an input to later error-law stress tests, not a sensor-only calibration.
The [ground tilt check](prediction-observed-development/ESA_GROUND_TILT_CLOSURE_RESULT.md)
reduces centered direction change error by 88–92% at the first stop and
30–38% at the second. Ground rate variation includes a component consistent
with tilt. Yaw and gyro-only variation remain unresolved, so the ground
data still do not calibrate the airborne error law.
The [full opened-flight parallel receiver check](prediction-observed-development/FULL_PARALLEL_GNSS_V2_RESULT.md)
finds a persistent decimetre-scale divergence in one PPP export during its
last fixed window, despite centimetre-scale relative agreement earlier. A
[receiver-speed split](prediction-observed-development/PARALLEL_GNSS_MOTION_PHASE_RESULT.md)
shows smaller fast-flight divergence and a larger low-speed discrepancy.
E02's next gate must allow time-varying receiver discrepancy and test absolute
withheld predictions; shared antenna agreement cannot certify true position.
The [Reykjavík station check](prediction-observed-development/ESA_FIXED_REFERENCE_WINDOW_RESULT.md)
verifies 61 observation times during the later ground stop. The fixed
receiver is 0.93 km away. The [paired source check](prediction-observed-development/ESA_FIXED_REFERENCE_PAIR_RESULT.md)
matches all 61 times with ten continuously tracked common satellites.
The [relative-motion check](prediction-observed-development/ESA_FIXED_REFERENCE_PHASE_RESULT.md)
finds 0.27 m north, 0.40 m east and 0.85 m up RMS disagreement with
the original aircraft GPS path. The [band check](prediction-observed-development/ESA_FIXED_REFERENCE_BAND_RESULT.md)
shows that both bands give the same discrepancy. Applying the [recorded
clock offsets](prediction-observed-development/ESA_FIXED_REFERENCE_CLOCK_RESULT.md)
to time, code and phase together leaves the vertical disagreement at
0.85 m RMS. The [direct Doppler comparison](prediction-observed-development/ESA_FIXED_REFERENCE_DOPPLER_RESULT.md)
completed both receiver tasks. The integrated aircraft path differs from
both position paths by about 15 m vertically RMS over the half-hour stop.
It cannot settle their sub-metre difference. The Greenland airborne
interval still lacks a nearby station file in the checked archives.
A [120-second fast-flight check](prediction-observed-development/PARALLEL_GNSS_120S_RESULT.md)
now finds 95th-percentile relative receiver changes of about 1–2.5 cm per
axis across 195 windows. It does not constrain common receiver error or the
much larger IMU-based forecast misses.
A [reported-precision comparison](prediction-observed-development/PARALLEL_GNSS_REPORTED_PRECISION_RESULT.md)
finds that 5.9% of the fast-flight `mosaic03` north positions differ from
`air1` by more than three times the summed reported precision scale. The
exports share an antenna, so this is a descriptive consistency check, not
an independent error calibration.
A [saved two-minute decomposition](prediction-observed-development/PARALLEL_GNSS_WINDOW_DECOMPOSITION_RESULT.md)
finds that 90–99% of the fast-flight relative mean-square receiver difference
comes from each window's persistent mean rather than within-window variation.
The next error-law test must allow persistent receiver discrepancy, while
absolute common error remains unmeasured.
A [saved 400/120 forecast rescore](prediction-observed-development/ESA_ALTERNATE_PPP_SCORING_RESULT.md)
uses all three PPP exports on the same 120 withheld epochs. Both complete
development settings retain the same large numerical model ordering. This
tests export choice on one flight, not common GNSS error or calibrated
independent replication.
The [changing-drift transfer check](prediction-observed-development/ESA_CHANGING_DRIFT_TRANSFER_RESULT.md)
contains the later receiver positions in all 20 forecast ranges, which overlap
across the matched models.
The [correction audit](prediction-observed-development/ESA_DRIFT_CORRECTION_AUDIT_RESULT.md)
finds that the term allowing jerk to change supplies about 3.84 km RMS of
the disc's 4 km correction. Receiver terms supply less than 0.14 m RMS.
[Removing the changing-jerk term](prediction-observed-development/ESA_NO_SNAP_ABLATION_RESULT.md)
restores specified-globe/disc separation at 28–29 later epochs on this flight.
The same change [misses 59 of 256 generated paths](prediction-observed-development/ESA_NO_SNAP_GENERATED_BACKCHECK_RESULT.md)
under the original coverage rule. Neither endpoint provides both coverage and
separation. Keep the reserved flights closed and test independently justified
inertial discrepancy assumptions against both requirements. Score complete
withheld paths with their temporal correlation as well as checking whether
individual coordinate ranges overlap.
The [whole-path replay](prediction-observed-development/ESA_JOINT_PATH_SCORE_RESULT.md)
favors the specified-field globe in both complete settings even with the full
law. The uncertainty scale still needs validation on fitted, known-model
histories before any independent aircraft decision.
The [first fitted known-model replay](prediction-observed-development/MATCHED_GENERATED_JOINT_SCORE_RESULT.md)
recovers 9–12 of 12 generated labels depending on the error assumptions.
Some still-globe cases rank as disc. The next gate needs independent
known-model histories and a predeclared adequacy and abstention rule.
The [provisional adequacy rule](prediction-observed-development/JOINT_SCORE_ABSTENTION_RESULT.md)
made six correct shape calls on the 12 development simulations. It abstained
on the paired route controls and all four ESA development settings. In the
complete ESA settings only the specified-field globe stayed compatible, but
the assumed scale was too large relative to its observed errors. Test the
uncertainty scale and fitted calibration jointly before a new aircraft decision.
An [affine software check](prediction-observed-development/CALIBRATED_JOINT_SCORE_RESULT.md)
keeps roughly 95% inclusion after estimating a common ninefold variance
change from earlier reports. It misses most histories when the receiver
variance changes only later. A fitted aircraft qualification must handle
error stability across the cut as well as calibration and scale.
The [saved scale sensitivity check](prediction-observed-development/JOINT_SCORE_SCALE_WINDOW_RESULT.md)
finds two disjoint adequacy ranges on the opened ESA flight, one per receiver
weighting assumption. Neither includes the original scale. This identifies
what a prospective fit-error model would need to explain and leaves the
original abstentions in place.
The [equal-horizon transfer check](prediction-observed-development/ESA_ROLLING_SCALE_TRANSFER_RESULT.md)
estimates the error scale from an earlier forecast on the same ESA flight.
The matched later forecast has 3.31–3.70 times the standardized squared error,
and using the earlier estimate leaves all candidates above the provisional
reference limit. Allow for changes across the cut before testing an
independent flight.
The [smooth-error diagnostic](prediction-observed-development/FORECAST_SMOOTH_ERROR_RESULT.md)
recovers all sixteen weighted scores and shows that removing a cubic
position trend leaves the later-to-earlier error ratio essentially intact.
A simple smooth offset cannot explain the scale change on that flight.
The [paired forecast check](prediction-observed-development/FORECAST_PAIR_INFORMATION_RESULT.md)
finds that at least 86% of the squared distance between candidates
survives a cubic error allowance on the saved paths. Calibration-induced
path changes and aircraft error still need independent qualification.
The [alternate-training forecast check](prediction-observed-development/FORECAST_FAMILY_MARGIN_RESULT.md)
retains at least 99.1% of the corresponding distance across the three
observed receiver choices and mixtures of their saved forecasts. This
narrows receiver-choice sensitivity on the opened flight. Shared error
and other changes to the mean path remain open.
The [in-flight Doppler check](prediction-observed-development/ESA_DOPPLER_CONTRAST_RESULT.md)
applies two observed displacement differences to the earlier-conditioned
shape score. They shift it by 31.5% and 25.8% of the certified gap,
while their difference shifts it by 5.7%. This quantifies sensitivity
to two motion reconstructions from the same aircraft antenna. Their
agreement leaves errors shared by all reconstructions unbounded.
A [shared-motion check](prediction-observed-development/ESA_SHARED_MOTION_GAP_RESULT.md)
shows that a constructed 0.71 m north-axis displacement within the
later window can span the fixed score's gap while position and velocity
are exactly unchanged at the ends. An independent reference must
constrain motion within the window to address this example.
The [carrier signature comparison](prediction-observed-development/ESA_SHARED_MOTION_CARRIER_RESULT.md)
finds that canceling the example needs about 4.9 mm per half-second
satellite range change. The archived satellite clock change is about
0.6 mm RMS and has a different pattern. Other shared error sources
remain open.
The [contrast-versus-common error check](prediction-observed-development/MODEL_CONTRAST_PARTITION_RESULT.md)
shows why rankings alone cannot qualify the covariance. The reduced law
with reported receiver weights recovers 12/12 labels but gives the
generating model excessive error in the distinguishing directions on
10/12 cases. Check the error in those directions separately before
freezing a decision.
The [split-window control](prediction-observed-development/SPLIT_CONTRAST_RESULT.md)
chooses the forecast direction separately from the data used to estimate
calibration. Its affine reference passes with disjoint windows and
breaks under data reuse or a later error change. Aircraft use still needs
a nonlinear calibration check and justified error bounds across the cut.
The [ESA training-window check](prediction-observed-development/TRAINING_WINDOW_GEOMETRY_RESULT.md)
shows severe local information loss after discarding the first 200
training reports, despite full numerical rank. Test directions fixed
in advance using independent inputs before giving up the full training
calibration on this flight.
The [generated direction-transfer check](prediction-observed-development/FORECAST_DIRECTION_TRANSFER_RESULT.md)
retains a median 67% of the weakest contrast using independent donors on
the same route and 20% using the other route. A common two-direction
template loses too much information on some paths. A [wider preflight](prediction-observed-development/WIDE_DIRECTION_PREFLIGHT_RESULT.md)
retains at least 97.1% of fixed-path separation on separate straight and
turning controls. Neither width expansion nor the best exact direction
provides useful power for every pair. Establish a prospective route and
error-information screen before a larger directional calibration.
The [training-route check](prediction-observed-development/RECEIVER_ROUTE_INFORMATION_RESULT.md)
uses the three fixed ESA development windows. More course change helps
the specified-field comparison, while a steadier window has stronger
zero-field shape contrast. Keep the separate contrasts in any future
screen. The calculation still assumes independently removable aircraft
rotation and does not clear the fit gate.
The [receiver motion precision check](prediction-observed-development/RECEIVER_MOTION_PRECISION_RESULT.md)
finds that ground velocity cannot supply that constraint. Even its
120-second course-rate proxy has a conditional uncertainty around
5°/h, versus a motion budget below 0.35°/h in the rate-only comparison.
Keep these proxy directions separate from measured body attitude.
The [native ESA forecast replay](prediction-observed-development/ESA_NATIVE_TANGENT_REPLAY_RESULT.md)
reproduces the 400/120 development forecast exactly and retains all 27
calibration derivatives. Its three weakest training directions have
3.7–8.7 times greater local RMS effect on later positions. The
[six finite-change checks](prediction-observed-development/ESA_TANGENT_REMAINDER_RESULT.md)
then measured up to 0.26 mm later RMS error at a normalized step of 0.01
and 25.7 mm at 0.10. This checks changes along individual directions in
one fit. The [three-model combined-change check](prediction-observed-development/ESA_MIXED_CALIBRATION_RESULT.md)
finds later interaction errors of 8–13 mm RMS at the larger step. The same
step in normalized parameters changes the earlier path far more in the
zero-field fits. The [earlier-cost comparison](prediction-observed-development/ESA_EARLIER_FIT_COST_RESULT.md)
matches increases in approximate training loss across all three models.
The bound from receiver white noise cannot certify any of the six steps
under the full covariance. The [original-weight replay](prediction-observed-development/ESA_ORIGINAL_WHITENING_RESULT.md)
saves and verifies the earlier whitening factors for all three models.
Four steps slightly exceed their diagnostic allowance, with maximum
disagreement of 0.000002804 between linear and exact loss changes.
The [calibration contrast check](prediction-observed-development/ESA_CALIBRATION_CONTRAST_RESULT.md)
then uses all 27 directions. The larger loss allowance bounds affine
closure at 9.96–11.60 m across raw forecast gaps of 1.44–4.00 km.
The [conditioned comparison](prediction-observed-development/ESA_CONDITIONED_CALIBRATION_RESULT.md)
reduces those gaps to 24–62 m. At least 99% of each gap remains
under the local affine calibration check. Exact propagation verifies
all 12 steps at 98% size. The next gate needs aircraft evidence for
the error law and a remainder bound over the full nonlinear region,
before evaluating absolute prediction accuracy.
The [future covariance control](prediction-observed-development/FUTURE_COVARIANCE_BRACKET_RESULT.md)
bounds the whole-path score when additional receiver scatter and drift
start after the cut. It enclosed all 768 in-range generated scores, but its
wider ranges make adequacy harder to establish. An aircraft test needs
independently supported bounds on the change.
The [native ESA error sensitivity](prediction-observed-development/ESA_NATIVE_FUTURE_ERROR_RESULT.md)
uses the three sealed forecasts and their original covariance factors.
The zero-field paths need 5.69–9.82 m of added random-walk endpoint
error to reach a unit mean squared standardized error. The
specified-field path is already below it, but its later standardized
error is 10.9 times its training error. The
[native equal-horizon comparison](prediction-observed-development/ESA_NATIVE_ROLLING_TRANSFER_RESULT.md)
then uses two previously held-out windows and finds a 4.06-fold
score increase under both IMU error descriptions. The growth is
concentrated in the east-ordered score channel, while the height-ordered
channel falls slightly. The [motion and error check](prediction-observed-development/ESA_INNOVATION_TRANSFER_RESULT.md)
finds 85.5% of the later east-ordered score in the 30 reports after
the recorded 13° course change. Stable channel-specific scales
estimated earlier transfer worse than a common scale. The
[straight-flight and heading-step checks](prediction-observed-development/ESA_MANEUVER_ERROR_RESULT.md)
then find 11.88 m height RMS on an additional entirely straight
holdout and under 1% score reduction from a permanent heading step
after the original turn. The [motion-dependent error check](prediction-observed-development/ESA_MOTION_ERROR_LAW_RESULT.md)
finds that a separate maneuver response improves the later score,
while a quadratic displacement describes 99.8% of the straight
holdout's height-error energy. Sharing one fitted scale across
both effects transfers poorly. The [component preflight](prediction-observed-development/ESA_COMPONENT_PREFLIGHT_RESULT.md)
finds zero information about maneuver variance in the earlier forecast
and separates it from steady error locally in the later forecast. Two
of three preselected training windows contain recorded maneuvers. The
[known-answer scale check](prediction-observed-development/COVARIANCE_SCALE_CONTROLS.md)
recovers separate scales on generated samples with a known mean and
abstains on quiet or confounded controls. The [fitted-path control](prediction-observed-development/FITTED_PATH_COVARIANCE_CONTROLS.md)
extends this to a linear training fit with errors shared across the cut.
In the [saved ESA training designs](prediction-observed-development/ESA_FITTED_SCALE_SUPPORT_RESULT.md),
less than 0.43% of the steady error pattern survives unrestricted local
calibration, compared with about 14.5% for maneuver error. A
[bounded replay](prediction-observed-development/ESA_BOUNDED_DRIFT_RESULT.md)
leaves under 1% of each tested steady pattern. Holding accelerometer
biases and gravity fixed still leaves under 1.4%. Even exact force
magnitudes at the [two ground stops](prediction-observed-development/ESA_GROUND_FORCE_SUPPORT_RESULT.md)
would raise the unrestricted retained energy only from about 0.42% to
0.46%. The [receiver-velocity check](prediction-observed-development/ESA_RECEIVER_ACCELERATION_RESULT.md)
finds up to 1.12 m/s² horizontal maneuver acceleration. At the same 96
centers, [receiver positions](prediction-observed-development/ESA_POSITION_ACCELERATION_RESULT.md)
give a median force-magnitude SD of 0.00044–0.00050 m/s² assuming
independence, but arbitrary time correlation raises the upper bounds
above the 0.001 m/s² drift scale in every case. Changing the support
width shifts magnitudes by more than switching between position and
velocity on the longer support. The [time-matched force check](prediction-observed-development/ESA_MATCHED_FORCE_RESULT.md)
then compares the receiver path with the raw accelerometer. A common
offset estimated on the other two windows leaves 0.005–0.007 m/s² RMS
in two windows and 0.065 m/s² in the third. The [fast-variation check](prediction-observed-development/ESA_FORCE_VARIATION_RESULT.md)
reduces the third window to 0.00090 m/s² by averaging the vectors for
0.1 seconds before taking magnitudes. Logged rotation accounts for only
a small part under the fixed-force-direction check. The [saved forecast comparison](prediction-observed-development/ESA_FAST_FORCE_TRANSFER_RESULT.md)
finds that using this variation to scale errors worsens both later log
scores. The [error-shape transfer check](prediction-observed-development/ESA_ERROR_SHAPE_TRANSFER_RESULT.md)
estimates corrections on the earlier portion of saved position errors.
Steady acceleration reduces later straight-flight height RMS from
16.43 to 0.16 m, while worsening north error. The maneuver response
reduces later east RMS from 1.04 to 0.48 m after the turn. The
[repeat-turn inventory](prediction-observed-development/ESA_REPEAT_TURN_RESULT.md)
identifies four non-overlapping opportunities on the opened flight,
including a turn in the opposite direction. The [input preflight](prediction-observed-development/ESA_REPEAT_TURN_INPUT_RESULT.md)
verifies timing, the training prefix and later angular exposure in all
four. Two windows have no training trigger, so a window-specific
maneuver scale would be unsupported there. The [fixed scoring qualification](prediction-observed-development/ESA_REPEAT_TURN_SCORING_RESULT.md)
checks a common predeclared scale and separate steady and maneuver
terms against generated errors. The [prepared forecast inputs](prediction-observed-development/ESA_REPEAT_TURN_MATERIAL_RESULT.md)
verify all four training-only bundles. The [forecast release qualification](prediction-observed-development/ESA_REPEAT_TURN_RELEASE_RESULT.md)
binds them to 16 fixed starts and verifies compatibility with reboot
recovery. It requires all starts to reach a terminal outcome and picks
each forecast by training cost before opening later positions. The
[scored comparison](prediction-observed-development/ESA_REPEAT_TURN_FORECAST_RESULT.md)
completed all 16 starts and eight scores. The turn allowance improved
every window, and the combined allowance scored best in three of four.
Later three-axis RMS error was 0.44–1.97 m. Even under the best-scoring
choices, normalized errors vary across windows on this one flight.
Absolute error calibration and independent flight testing remain open.
The [steady-course controls](prediction-observed-development/ESA_STRAIGHT_CONTROL_PLAN.md)
give each turn a nearby unused comparison on the same development flight.
The input stage verified all 12 files. The forecast study then closed
all 16 fits under manifest SHA-256
`5e0bbc88c422cf92a1962017b79603bb84e28e9a105c48fa8a9f090bb75685ca`.
The [steady-course results](prediction-observed-development/ESA_STRAIGHT_CONTROL_RESULT.md)
cover eight forecasts scored against later GPS positions. Reassigning
the time pattern from the matched turns worsened every score, while
the steady uncertainty allowance improved every score. The mean
squared standardized error with that allowance ranged from 0.094 to 0.622.
A [saved-score scale check](prediction-observed-development/ESA_COMMON_SCALE_CHECK.md)
finds no common covariance multiplier under the joint Gaussian reference,
even when steady flight and turns are checked separately. A [smooth-error projection](prediction-observed-development/ESA_SCORED_PATH_SHAPE_RESULT.md)
explains 82% of the largest steady-course joint error with a smooth term.
After projection, turning errors still vary from 0.25 to 2.98 in mean
squared standardized units. An absolute criterion needs to allow smooth
path discrepancy and better account for the variation in turn errors.
The [held-pair scale comparison](prediction-observed-development/ESA_COMPONENT_SCALE_TRANSFER_RESULT.md)
puts one of eight windows inside the reference with either the original
or common fitted scale. The three-component optimizer meets its stopping
rule in one of eight checks, and both windows in that check miss the reference.
The [same-likelihood whitening check](prediction-observed-development/ESA_WHITENED_SCALE_TRANSFER_RESULT.md)
also passes one of eight stopping checks. Both withheld windows in that
fit miss the reference. The [full variance-range check](prediction-observed-development/ESA_COMPONENT_SCALE_FEASIBILITY_RESULT.md)
finds that no scales can fit all eight windows under either description.
The hardest turn requires over 14 times the native variance allowed by
one steady window. The [axis and time check](prediction-observed-development/ESA_FORECAST_ERROR_LOCALIZATION_RESULT.md)
shows that each axis of the hardest turn exceeds the whole-path limit.
Future changes need to address horizontal as well as vertical errors.
The [forecast timing check](prediction-observed-development/ESA_FORECAST_TIME_SHIFT_RESULT.md)
finds that a constant shift learned from other windows leaves seven of eight
outside the reference. Even the best retrospective shift barely changes the
worst turn. This removes simple path registration as a useful correction
under the working covariance.
The [motion-dependent innovation check](prediction-observed-development/ESA_MOTION_INNOVATION_SCALE_RESULT.md)
improves the held-out joint score in six of eight windows. It still puts
one window inside the error reference, with a large miss on a steady leg.
This tested rule cannot serve as the confirmation error law.
Allowing [separate quiet scales by innovation slot](prediction-observed-development/ESA_AXIS_INNOVATION_SCALE_RESULT.md)
improves all eight scores against the shared motion rule and reaches the error
reference on two windows. Separate turn scales do worse on the hardest turn.
Neither alternative clears the development screen.
The [continuous scale check](prediction-observed-development/ESA_AXIS_SCALE_COMPATIBILITY_RESULT.md)
finds one shared setting for the four steady windows, with a much wider
height variance than the donor-only fits chose. The all-window search
leaves 661 open boxes per error law and gives no all-window decision.
The [continuous reference transfer](prediction-observed-development/ESA_SCALE_REFERENCE_TRANSFER_RESULT.md)
fits all six donor windows in every fold but only three of eight omitted
windows meet the reference. The held-out log score worsens. Optimizing the
reference directly still leaves the aircraft error law unqualified.
The [persistence test](prediction-observed-development/ESA_INNOVATION_PERSISTENCE_RESULT.md)
improves the omitted log score on all eight windows with the earlier variances
fixed. Five fall below the joint reference and one above. The next comparison
now [estimates persistence and variance together](prediction-observed-development/ESA_JOINT_PERSISTENCE_RESULT.md)
on the donors. Six of eight omitted windows meet the reference. All starts
reach the evaluation cap. The [saved gradient check](prediction-observed-development/ESA_JOINT_PERSISTENCE_STOPPING_RESULT.md)
reproduced eight of eight donor scores and found feasible descent in every
fold. The [bounded analytic comparison](prediction-observed-development/ESA_JOINT_PERSISTENCE_ANALYTIC_RESULT.md)
passed all eight stopping checks. Both input conventions still place the
same six of eight windows inside the reference. The [sequential error audit](prediction-observed-development/ESA_PERSISTENCE_WINDOW_DIAGNOSTIC_RESULT.md)
finds that the steady miss is spread through all three thirds and the turn
miss occurs during and after the maneuver. Other steady and turning windows
pass, so the results give no basis for a uniform change in either setting.
The [training-history replay](prediction-observed-development/ESA_PERSISTENCE_HISTORY_RESULT.md)
accounts for earlier turns under the fixed 15-second decay. It slightly
lowers the steady window's score and leaves both misses outside the reference.
Allowing [whole-window variance to vary](prediction-observed-development/ESA_WINDOW_SCALE_MIXTURE_RESULT.md)
improves the omitted log score under both input conventions and brings
the low-error turn inside the reference. The high-error steady window
still exceeds it.
Substituting [two alternate GPS solutions](prediction-observed-development/ESA_FORECAST_RECEIVER_TRANSFER_RESULT.md)
brings that steady window inside but reduces the total within the
reference to three or two of eight. Receiver-specific error is now a
transfer requirement for the working covariance.
The [receiver difference covariance](prediction-observed-development/ESA_RECEIVER_CONTRAST_COVARIANCE_RESULT.md)
predicts omitted differences well enough to carry forward. It leaves
the slowly varying component and common GPS error open.
The [replacement check](prediction-observed-development/ESA_RECEIVER_COVARIANCE_COMPATIBILITY_RESULT.md)
finds that the estimated receiver term exceeds the working forecast
covariance in every window. Direct substitution cannot be used.
Refitting a [shared term beside the receiver terms](prediction-observed-development/ESA_ADDITIVE_RECEIVER_COVARIANCE_RESULT.md)
improves predictive log scores. The original receiver meets the reference
in two of eight windows, down from seven. The model still lacks a
transferable account of common and receiver-specific errors.
In a separate interval, [raw carrier changes only partly track the
GPS position differences](prediction-observed-development/ESA_RAW_PHASE_PPP_CLOSURE_RESULT.md).
At one second, the later position differences do worse than predicting
zero carrier difference for all three pairs.
The [longer-block comparison](prediction-observed-development/ESA_RAW_PHASE_PPP_TIMESCALE_RESULT.md)
also finds no consistent agreement for pairs containing `air1`.
Use a broader comparison of the position solutions to test whether their
relative error patterns transfer across the development flight.
In the [97-to-98-window chronological test](prediction-observed-development/ESA_PPP_COVARIANCE_CHRONOLOGY_RESULT.md),
the early model captures faster relative fluctuations but underestimates
the late shifts in relative position. Fixed receiver covariances alone
cannot model those shifts.
The [offset forecast](prediction-observed-development/ESA_PPP_OFFSET_FORECAST_RESULT.md)
cuts the typical short-lead offset error sharply by using an earlier
receiver comparison. Its predicted uncertainty still falls far short
of actual variation, even at two minutes.
Keep the independent flight groups closed until the error law passes the
development gate.
The [matched path check](prediction-observed-development/MATCHED_SHAPE_DRIFT_RESULT.md)
shows why the smooth correction needs a bound. In four paired forecasts
with the same background field, over 99.9% of the squared distance
between globe and disc paths lies in nine smooth directions. The RMS
separation in those directions is 69.50–1,441.19 m. On one exact ESA pair,
conditioning on the earlier positions reduced the raw gap from 1,443 m
to 7.24 m RMS. The part outside the smooth terms stayed near 0.76 m RMS.
The [forecast boundary check](prediction-observed-development/SHAPE_FORECAST_BOUNDARY_RESULT.md)
retains at least 98.9% of the squared weighted separation after omitting
the first 20 of 120 forecast reports. A [local calibration bound](prediction-observed-development/CONDITIONED_SHAPE_CALIBRATION_RESULT.md)
leaves at least 98.28% of the conditioned shape distance under both
tested earlier-loss allowances. The remaining checks are nonlinear
calibration error over the whole allowed region and the real-aircraft
covariance of the smaller path differences.
The [nonlinear error targets](prediction-observed-development/SHAPE_REMAINDER_HEADROOM_RESULT.md)
show that the local parameter box alone is insufficient. A uniform
earlier remainder norm of 0.1 per model would leave at least 12.78
standardized units for their combined later projected remainder.
The [exact probe replay](prediction-observed-development/SHAPE_REMAINDER_WITNESS_RESULT.md)
found an earlier remainder of 0.160 at a disc point that clearly fails
the original training-loss limit. Certifying 0.1 therefore requires
enclosing the smaller, feasible region instead of the full parameter box.
Near-limit feasible probes had remainders below 0.000086.
The [directional error conversion](prediction-observed-development/SHAPE_REMAINDER_METRES_RESULT.md)
turns the later proof target into 4.03 cm per coordinate at each report,
provided the earlier standardized remainder bound of 0.1 can be proved.
The shared-prefix interval predictor uses the archived height-dependent
gravity law. A [generated growth check](prediction-observed-development/SHAPE_GRAVITY_HISTORY_RESULT.md)
kept the largest remainder below 0.315 mm at 39.875 seconds on a coarse
grid. The [outward-rounded reference](prediction-observed-development/SHAPE_INITIAL_FORCE_RESULT.md)
then passed the original zero-centred checks. It used the
[shared force-integral calculation](prediction-observed-development/SHARED_FORCE_INTEGRALS.md)
to make one packet pass for all report times. The
[archived-packet preflight](prediction-observed-development/ESA_SHAPE_PREFIX_PREFLIGHT_RESULT.md)
matched two disc positions, while the globe bound reached its time limit.
An [exact arithmetic optimization](prediction-observed-development/ESA_SOURCE_TRANSFER_CHECK.md)
then completed both at the same time limit and reproduced the disc reports
byte for byte. Improve full-history packet speed and retain the shared
calibration terms in the earlier-fit constraints before testing the
4.03 cm target over the complete record.
The [recorded packet profile](prediction-observed-development/ESA_PACKET_BOUND_PROFILE_RESULT.md)
reproduced both original reports for each candidate. Runtime is spread
across transport, source bounds and Python buffer handling. The [width-cache benchmark](prediction-observed-development/ESA_PACKET_WIDTH_CACHE_RESULT.md)
reproduced the archived bounds and missed the speed gate. With the original
arithmetic, the [recorded prefix growth check](prediction-observed-development/ESA_PACKET_BOUND_GROWTH_RESULT.md)
crosses the 4.03 cm target by 4.55 seconds for both candidates. At 9.55
seconds, the propagated position term accounts for about 0.41 m in each
case. The [position-budget trace](prediction-observed-development/ESA_POSITION_BOUND_BUDGET_RESULT.md)
attributes 98–99% of the largest accumulated departure to residual velocity.
The other terms, including the lever arm, still exceed the uniform target
at 9.55 seconds. Rework the shared calibration error bound before a full-history
run. The result leaves the scientific comparison open.
The [full shared coefficient check](prediction-observed-development/ESA_SHARED_PROFILE_RESULT.md)
shows that linking terms across reports nearly cancels the clock, lever
and reference-acceleration contributions to the shape score. The nine
force-transform terms remain too wide when their limits vary separately.
The [coupled rotation and gain calculation](prediction-observed-development/ESA_FORCE_SCORE_RESULT.md)
limits the total shared reduction to 8.55 standardized units under the
fixed 3 cm covariance. The remaining gates are the earlier feasible-region
limit and a sufficient 1.35 cm unshared position bound under that covariance.
The [joint earlier-loss bound](prediction-observed-development/ESA_LINKED_TRAINING_SUPPORT_RESULT.md)
kept all 51 coordinates and limited the combined reduction to about 103
units versus 25.41 units of nominal separation. The earlier observations
help, but the box still lets shared coefficients vary independently.
The [joint force check](prediction-observed-development/ESA_JOINT_FORCE_SUPPORT_RESULT.md)
applied the same force map to the earlier and later score. The combined
bound fell by less than one standardized unit in every scenario. The
decomposition traced nearly all the remaining bound to the projected
training constraint and the physical parameter box.
The [feasible-point check](prediction-observed-development/ESA_CALIBRATION_WITNESS_RESULT.md)
shows that independently varying shared terms can produce 102.35 units
of combined movement. The same physical proposals fail earlier GPS
when all shared terms come from one calibration. The
[whole-box static map](prediction-observed-development/ESA_COUPLED_TRAINING_SCORE_RESULT.md)
retained every linked example but left a wider bound than the
force-specific result. The earlier loss breakdown identifies the
reference-acceleration remainder and force transform as the main
contributors. The current inequalities already exclude both saved
independent-coefficient examples. A [direct support calculation](prediction-observed-development/ESA_DIRECT_TRAINING_SCORE_RESULT.md)
bounded the numerical gap to about 0.04 units per candidate and found
feasible combined movements around 80 units. Further solver refinement
cannot resolve the 25.41-unit separation under these same inequalities.
The [bias and force product check](prediction-observed-development/ESA_ACCELERATION_PRODUCT_SCORE_RESULT.md)
tightened the combined upper bound to 77.77 units at zero earlier unshared
error. A feasible disc example under those constraints still moves
38.54 units. Use smaller physical ranges that together cover the original
box to tighten the shared map further. The
[eight-range attitude cover](prediction-observed-development/ESA_ATTITUDE_COVER_SCORE_RESULT.md)
reduced the combined bound from 78.52 to 60.97 units at an assumed
earlier unshared error norm of 0.1. The [32-range refinement](prediction-observed-development/ESA_ATTITUDE_REFINEMENT_SCORE_RESULT.md)
left those maxima unchanged because one child per parent kept the
parent certificate. The [earlier-loss check](prediction-observed-development/ESA_ATTITUDE_FEASIBILITY_RESULT.md)
excluded 17 of the 26 high-bound ranges, including all eight that
retained their parent bound. The remaining cover bounds 54.01 units
of movement. The [scaled survivor check](prediction-observed-development/ESA_ATTITUDE_SURVIVOR_SCORE_RESULT.md)
verified a disc point that moves the forecast 31.86 units under
the relaxed constraints. The combined upper bound is 54.00 units.
Replaying both reported points with one physical calibration caused
both to fail the earlier GPS check. The [linked search](prediction-observed-development/ESA_LINKED_PHYSICAL_SCORE_RESULT.md)
found feasible examples moving 12.54 units combined at an assumed
earlier unshared error norm of 0.1, and 0.43 units without it.
The [full integrating-model replay](prediction-observed-development/ESA_LINKED_PHYSICAL_REPLAY_RESULT.md)
confirmed 0.432 units of combined movement for the two points that
still pass the original earlier loss limit. Both points chosen under
the 0.1 allowance fail that original limit. At zero assumed earlier
unshared error, the saved certificates still permit 53.66 units of
combined movement. The [linked directional bounds](prediction-observed-development/ESA_LINKED_DIRECTIONAL_RESULT.md)
tightened four of nine ranges relative to the original cover. The
global bound stayed at 53.66 units. The remaining disc maximum in
range 2/3 drives the unresolved result. A new direction or a different
way to constrain that range is needed before bounding integration
error over the full history. In parallel, continue the independent
measurement-contribution and aircraft-error checks.
The [interval derivative check](prediction-observed-development/ESA_LINKED_MONOTONE_RESULT.md)
finds no fixed derivative signs in 165 graph directions within their
respective boxes. Its 53.04-unit bound stays unchanged. Test a direction
that suppresses the calibration effects of both model forecasts.
The [joint calibration projection](prediction-observed-development/ESA_CALIBRATION_ORTHOGONAL_RESULT.md)
leaves a positive affine gap only after suppressing the full
calibration span. It allows a uniform nonlinear error of just
0.48 µm per coordinate, outside current integration support. The
[maximum-margin test](prediction-observed-development/ESA_CALIBRATION_MAXIMUM_MARGIN_RESULT.md)
then finds a 12.18 cm allowance with a broader direction. That
direction puts 46.5% of its absolute weight on earlier coordinates.
The [first conditioned search](prediction-observed-development/ESA_CALIBRATION_CONDITIONED_MARGIN_RESULT.md)
reaches its iteration limit. The [compact forecast check](prediction-observed-development/ESA_COMPACT_FORECAST_MARGIN_RESULT.md)
uses the state at the cut and brackets the best conditioned allowance
at 2.25 cm, below the earlier 4.03 cm integration reference. The saved
affine problem has now been solved to within 0.42 µm. The
[integrated-error check](prediction-observed-development/ESA_INTEGRATED_CONTRAST_SUPPORT_RESULT.md)
then puts the allowance for interval-average velocity error at
4.69 mm/s per axis, almost entirely weighted after the forecast cut.
The [full replay](prediction-observed-development/ESA_CONTRAST_REPLAY_RESULT.md)
then changes the contrast by less than 0.0042% combined at the two
points meeting the earlier-loss limit. The two rejected points also
change it by less than 0.073% individually. Aircraft prediction still
requires a bound over all admissible calibrations.
The [earlier-loss check](prediction-observed-development/ESA_CONTRAST_TRAINING_SUPPORT_RESULT.md)
excludes both points behind the box-only upper bound. The lower
allowance stays at 2.25 cm. The calculation now needs a bound that
uses the earlier data in directions relevant to the forecast score.
The [targeted check](prediction-observed-development/ESA_CONTRAST_SCORE_ALIGNED_RESULT.md)
tests six directions from the archived calibration matrix and leaves
the lower allowance unchanged. Work shifts to the receiver and aircraft
error checks before further tuning this contrast.

The [twenty-group GPS-only comparison](prediction-group-transfer/REMAINING_GPS_BASELINE_RESULT.md)
completed all 40 forecasts using the original receiver epochs. The IMU
forecast improved horizontal RMS on all 18 cuts with a passing original
IMU start, across 13 groups. Height outcomes were mixed at the later
cut. The 22 unavailable IMU comparisons remain in the ledger. This is a
retrospective control of overall inertial forecast performance. A separate
matched channel comparison remains needed to isolate the gyroscope.
An [earlier-only force-direction alignment](prediction-observed-development/ESA_FORCE_DIRECTION_TRANSFER_RESULT.md)
then tests prediction across sixteen existing supports from the opened
ESA flight. It favors the globe at nominal calibration with either
matched background field. The +0.10 m/s² X correction reverses the
retained-field comparison. The result retains calibration and absolute
accuracy as open gates for C04.
The [earlier-only bias selection](prediction-observed-development/ESA_DIRECTION_BIAS_TRAINING_RESULT.md)
then favors the globe in all 18 later direction comparisons even when
each candidate estimates its own X bias. Excluding the high positive
bias range for the retained-field globe would require external support
for a direction discrepancy below about 0.013° at fixed predictions and
fixed remaining calibration. Other gyro-field assumptions select
positive biases. Joint calibration remains open.
The [six-coordinate accelerometer check](prediction-observed-development/ESA_DIRECTION_ACCEL_CALIBRATION_RESULT.md)
then preserves the globe preference in all 18 later comparisons with
the gyro fixed. A common gain scale is unobservable from direction alone,
and 99 of 108 starts use at least one calibration bound. The gyro and the
aircraft direction-error model remain open gates for C04.
The [joint gyro and accelerometer check](prediction-observed-development/ESA_DIRECTION_JOINT_CALIBRATION_RESULT.md)
then finds a smaller shape gap with the specified field retained. One
GLONASS setting favors the disc by 0.006°. The matched zero-field results
still favor the globe. Pointwise gyro replays pass the approximation
check, while global calibration and a direction-error law remain open.
The [exact earlier gradient audit](prediction-observed-development/ESA_DIRECTION_EXACT_GRADIENT_RESULT.md)
finds no saved joint proposal meets the original stopping limit on the
exact packet model. Qualify a bounded correction using the exact
derivatives before interpreting the joint result as a stopped fit.
The [bounded exact correction](prediction-observed-development/ESA_DIRECTION_EXACT_CORRECTION_RESULT.md)
now passes all 36 local stopping checks with unchanged bounds. The
ranking is 17 globe and one disc, with the disc result in the same
retained-field GLONASS setting as before. The direction-error law,
global calibration envelope and independent prediction remain open.
The [velocity source swap](prediction-observed-development/ESA_DIRECTION_VELOCITY_TRANSFER_RESULT.md)
finds that the reversal follows the GLONASS training source in the
retained-field 11-report setting. Changing the later scoring source alone
never reverses the ranking. Receiver-dependent calibration still matters
even after all exact stops pass.
The [shared-calibration check](prediction-observed-development/ESA_DIRECTION_POOLED_CALIBRATION_RESULT.md)
then gives a smaller later error for the globe in every comparison when
training uses all three sources or any two of them in the previously
reversed setting. The minimum margin across those conditions is only
0.00125°. Shared receiver errors and independent angular accuracy are
the gates for interpreting this result beyond the opened flight.
The [eight-window transfer](prediction-observed-development/ESA_DIRECTION_WINDOW_TRANSFER_RESULT.md)
preserves the globe ranking in all 48 settings at nominal and fixed
pooled calibration. The pooled calibration worsens the retained-field
globe error by a median factor of 4.6. Small training error therefore
does not justify assuming that the fitted calibration transfers.
The [angle-pair replay](prediction-observed-development/ESA_DIRECTION_ANGLE_PAIRS_RESULT.md)
preserves all 48 rankings without fitting starting orientation. This
provides a pose-independent check of the direction changes. The smallest
paired RMS gap is 0.0007° before the
[antenna offset correction](prediction-observed-development/ESA_DIRECTION_LEVER_ARM_RESULT.md).
Accounting for the published 2.12 m offset preserves all 48 rankings.
The smallest paired gap is then 0.0162°. The correction needs no new
calibration fit. An independently justified angular error scale remains
open, and the independent flight groups remain reserved.
The [matched GIRAFE check](prediction-observed-development/ESA_GIRAFE_FORCE_OVERLAP_RESULT.md)
adds a separate force measurement on the same eight windows. The two
devices agree on force changes while GIRAFE reads 26–29 mm/s² lower on
average. The [two-instrument force contrast](prediction-observed-development/ESA_GIRAFE_FORCE_CONTRAST_RESULT.md)
finds that the predicted shape differences are below both observed
comparison scales in every tested receiver and gravity setting. This
checks the force-only interpretation on the development flight. An
absolute error model and separate validation flights remain open.
The [chronological error check](prediction-observed-development/ESA_GIRAFE_FORCE_ERROR_LAW_RESULT.md)
finds that allowing a shared error across a window improves the force
disagreement score on all four later windows at both widths. This
supports keeping a persistent error term in development. It remains
a relative comparison between two sensors on one flight.
The [airport gravity check](prediction-observed-development/ESA_GIRAFE_GROUND_TIES_RESULT.md)
compares ground means with the campaign's independent apron
measurements. iMAR agrees within 0.45 mm/s² and GIRAFE within
0.011 mm/s² on the retained stops. The difference between the two
sensors grows by more than a factor of ten in flight using the
same magnitude statistic. The aircraft error model needs to account
for that change in conditions.
The [matched-averaging replay](prediction-observed-development/ESA_GIRAFE_FORCE_BANDWIDTH_RESULT.md)
removes about 98% of the median airborne gap by using the same
time cells before computing force magnitude. One window retains
a much larger disagreement. The [matched error-law test](prediction-observed-development/ESA_GIRAFE_MATCHED_ERROR_LAW_RESULT.md)
uses the matched force summaries and retains the variable-setting
window. Training on the constant setting gives later disagreements
of 0.165 and 0.062 mm/s² RMS on this flight. Absolute errors and
between-flight transfer remain open.
The [velocity error calculation](prediction-observed-development/ESA_FORCE_VELOCITY_ERROR_RESULT.md)
propagates the receiver's reported velocity covariance through both
shape predictions. Shared errors partly cancel in the comparison of
predictions. The assumed time correlation can still move the absolute
force uncertainty by orders of magnitude. Its actual scale needs
receiver evidence beyond the printed uncertainties.
The [position derivative comparison](prediction-observed-development/ESA_FORCE_POSITION_DERIVATIVE_RESULT.md)
uses the same force supports. It improves agreement across receiver
products while increasing typical force error against GIRAFE from
1.30 to 3.62 mm/s². Receiver agreement alone leaves this common
prediction error unmeasured.
The [direction replay](prediction-observed-development/ESA_DIRECTION_RECEIVER_DERIVATIVE_RESULT.md)
preserves the globe–disc order in all 576 settings across both
derivative methods and three receiver products. One position-derived
window still misses the measured direction changes by about a degree.
On its largest acceleration discrepancy, applying both derivative
methods to the same reported velocities reproduces nearly all the
difference. The [matched receiver response](prediction-observed-development/ESA_MATCHED_RECEIVER_RESPONSE_RESULT.md)
reduces the largest difference between prediction methods from 1.017°
to 0.030° while retaining all 576 rankings. The force magnitude still
has far smaller separation than its error against GIRAFE. A
[receiver-only selection](prediction-observed-development/ESA_DIRECTION_HOLDOUT_SELECTION_RESULT.md)
saves eight disjoint windows across both legs of the development recording.
The [sealed forecast check](prediction-observed-development/ESA_DIRECTION_HOLDOUT_SCORE_RESULT.md)
finds a smaller globe error in all 64 comparisons with the specified field
retained. The strongest turn favors the disc in all eight zero-field
settings. With specified field removal the same turn changes preference
when the antenna correction is applied. The motion and field dependence on
this new window needs to carry into the independent-flight accuracy rule.
The [field-range check](prediction-observed-development/ESA_DIRECTION_HOLDOUT_FIELD_RANGE_RESULT.md)
bounds the best shape scores over every possible fraction of the specified
field retained in the gyro, plus the zero-field case. All 64 comparisons
favor globe with a gap of at least 0.0160° RMS. Develop and test an error
rule on independent flights after qualifying the motion and receiver errors.
The [alternate receiver check](prediction-observed-development/ESA_DIRECTION_HOLDOUT_RECEIVER_RESULT.md)
keeps the globe preference in all 64 first-leg comparisons from the two
alternate exports. The second-leg half-second schedule matches neither
export within 2 ms. The [whole-second check](prediction-observed-development/ESA_DIRECTION_HOLDOUT_CLOCK_RESULT.md)
matches all 400 queries in each of those four cells across all three
exports. The [scores on the common clock](prediction-observed-development/ESA_DIRECTION_HOLDOUT_CLOCK_SCORE_RESULT.md)
preserve all 96 field-range preferences and the zero-field reversal on the
turn. Receiver processing sensitivity is now measured on both legs. The
[GIRAFE platform log](external-imu-data/ESA_GIRAFE_187.md) offers a second
sensor check if its timing and measurement channels can be established. The
[bounded probe](prediction-observed-development/ESA_GIRAFE_PLATFORM_PROBE_RESULT.md)
finds 381 complete interior rows across three ranges. The clock follows
the same 1,024 Hz pattern as the prefix. The [force-magnitude timing result](prediction-observed-development/ESA_GIRAFE_PLATFORM_TIMING_RESULT.md)
failed its anchor requirement. Two later excerpts point to the same
clock offset. The [horizontal checks](prediction-observed-development/ESA_GIRAFE_PLATFORM_COMPONENT_TIMING_RESULT.md)
do not corroborate it with the tested axis mapping. Next, test the candidate
vertical channel on new excerpts. The [fixed-offset result](prediction-observed-development/ESA_GIRAFE_PLATFORM_VERTICAL_HOLDOUT_RESULT.md)
finds the same best offset in all three searches, but only one reaches
the minimum correlation. The [vertical response check](prediction-observed-development/ESA_GIRAFE_PLATFORM_VERTICAL_RESPONSE_RESULT.md)
finds correlations above 0.93 after 1.1-second averaging. The
[cross-instrument check](prediction-observed-development/ESA_GIRAFE_PLATFORM_IMAR_FORCE_RESULT.md)
matches two excerpts against the separate iMAR accelerometer. The middle
excerpt shows weaker force changes and fails even at its best shift. Timing
and gyroscope channel qualification remain open.
The [local rate convention screen](prediction-observed-development/ESA_GIRAFE_PLATFORM_RATE_RESULT.md)
finds modest tenth-second agreement with radians per second in the original
axis order. The same convention increases one-second error in all three
excerpts, leaving the rate mapping too uncertain for a separate angle check.
The [ground replay](prediction-observed-development/ESA_GIRAFE_GROUND_RATE_RESULT.md)
finds that all three iMAR force comparisons peak 0.1 seconds earlier, with
correlations above 0.95. Each misses the fixed-time requirement, and its
platform rates increase direction errors at both separations. The shift
needs a separate check before using the platform as an airframe reference.
The [finer comparison](prediction-observed-development/ESA_GIRAFE_FINE_LAG_RESULT.md)
still selects a 100 ms earlier shift on the ground. The best shifts on two
airborne clips differ by 140 ms at the same averaging width, and the middle
clip has no strong match. Further use as an angular reference needs an
independent clock and response check.
A [fixed-forecast receiver-shift bound](prediction-observed-development/ESA_FIXED_FORECAST_RECEIVER_MARGIN_RESULT.md)
shows that the same ESA development scores would need about 1.3 km of
per-report displacement to tie the two globe forecasts and 2.0 km to tie
the globe and disc forecasts. This is a sensitivity of sealed predictions,
not an absolute receiver accuracy claim or a substitute for refitting and
independent validation.
The [two alternate training inputs](prediction-observed-development/ESA_ALTERNATE_TRAINING_MATERIAL_RESULT.md)
are now frozen from the first 400 reports of the opened ESA flight. Their
coordinate changes are centimetre-scale and only the three position fields
differ from the original input, as an independent 400-row source audit verifies.
A [separate bounded six-fit study](prediction-observed-development/ESA_ALTERNATE_TRAINING_REFIT_RESULT.md)
has closed with six numerical passes. Both alternate training sources retain
the original model ordering on the same 120 later reports; the preferred
specified-field globe's total RMS is 4.74–5.23 m versus 5.23 m with the
original training source. This narrows receiver-export sensitivity on one
development flight, while shared receiver error and aircraft uncertainty
remain unqualified.
A [joint future-path profile](prediction-observed-development/JOINT_FUTURE_PROFILE_RESULT.md)
and [joint whitening](prediction-observed-development/CONDITIONAL_JOINT_PROFILE_RESULT.md)
pass software controls. Their [sealed generated replay](prediction-observed-development/GENERATED_JOINT_PROFILE_SAVED_RESULT.md)
finds that full-range calibration steps make the native path differ from its
local tangent by metres to tens of metres. The two replay tasks remain
terminal technical failures, with a separate saved-data audit verifying the
three completed profiles and their receipts. Do not rank models by those
linear costs. A local or fully nonlinear compatibility method needs a new
finite qualification; earlier-only prediction and aircraft error-law work
remain the higher-priority gates.
The [radius-0.1 generated check](prediction-observed-development/GENERATED_LOCAL_PROFILE_RESULT.md)
then passed its complete technical task but still found decimetre-to-metre
nonlinear tangent error. It does not qualify a joint-profile decision;
earlier-only prediction remains primary.
The [bounded whole-path check](prediction-observed-development/BOUNDED_JOINT_PATH_RESULT.md)
requires one calibration compatible with both the earlier reports and the
later path. It agrees with a separate calculation on all 256 affine control
paths, including a true calibration at its bound. Before applying it to
aircraft, establish nonlinear approximation bounds across the earlier
calibration region and qualify the covariance law.

Priority shows the order of work. “Software checked” means a calculation passed
known-answer tests; it does not mean the aircraft result has been independently
validated.

| ID | Priority | Status | Work |
|---|---|---|---|
| F01 | Foundation | Complete | [Group related recordings](PROVENANCE_VERIFICATION.md) so overlapping stretches are not counted as independent flights. |
| F02 | Foundation | Complete | [Reserve separate ESA flight groups](PROVENANCE_VERIFICATION.md) for a later independent test. |
| C01 | First | Complete | [Check the basic motion calculations](ilvis0-measurement-contribution/README.md). |
| C02 | First | Targeted aircraft checks complete; common error unbounded | The [six-direction check](prediction-observed-development/ESA_CONTRAST_SCORE_ALIGNED_RESULT.md) leaves the 2.25 cm lower allowance unchanged. The [full replay](prediction-observed-development/ESA_CONTRAST_REPLAY_RESULT.md) changes the contrast by less than 0.073% at each checked point. Two [observed Doppler paths](prediction-observed-development/ESA_DOPPLER_CONTRAST_RESULT.md) each shift the score by less than one third of the gap. Aircraft uncertainty remains open. |
| C03 | First | Matched development contrast complete in two settings; aircraft range unqualified | The original [256-case generated gate](prediction-observed-development/integrated-drift-v2-validation/RESULT.md) failed. A separate [fresh 256-case check](prediction-observed-development/threshold-42-validation/RESULT.md) passed its frozen gate with a wider 4.2 threshold. A [24-fit matched ESA development study](prediction-observed-development/ESA_400_120_MODEL_MATRIX_RESULT.md) closed with 20 numerical passes. Both complete profiled-removal settings favor globe on withheld positions and pass the preferred-fit physical screen; two zero-removal settings abstain after four [flat-model stopping failures](prediction-observed-development/ESA_400_120_MODEL_MATRIX_STOPPING.md). Saved derivatives rule out simple cost-subtraction rounding as the cause of the rejected full steps. None of this calibrates prediction uncertainty on an aircraft. Next: justify the observed error range and test the frozen method on independent flights; reserved ESA groups remain closed. |
| C04 | First | Force-only checks leave shape unresolved | Shared GPS perturbations clear the [necessary force inequalities](ilvis0-measurement-contribution/SHARED_FORCE_WITNESS_RESULT.md), with full-IMU rankings preserved. The [ESA two-instrument check](prediction-observed-development/ESA_GIRAFE_FORCE_CONTRAST_RESULT.md) finds sensor and receiver differences larger than the force-only shape difference. The [NCAR RF04 intake](ilvis0-measurement-contribution/NCAR_RF04_INTAKE.md) is ready for a separate whole-second motion check; the flight file and independently supported peak motion limits remain open. |
| V01 | First | 24/24 software controls passed | The [revised known-answer comparison](ilvis0-near-zero-forecast-controls/README.md) passed every generated case under its fixed work limit. This checks the calculation, not prediction accuracy on aircraft. |
| V02 | First | Retrospective NASA position checks passed. ESA uncertainty remains open. | All 104 saved NASA forecasts scored in the [fixed position check](prediction-group-transfer/ACCURACY_MARGIN_RESULT.md) meet its limits. They are development forecasts. On one opened ESA flight, the same forecasts and Student reference admit [seven, three or two of eight windows](prediction-observed-development/ESA_FORECAST_RECEIVER_TRANSFER_RESULT.md) depending on GPS solution. Aircraft prediction coverage remains open. |
| L01 | Diagnosis | Faster globe solver verified on one development recording | The [scope audit](mixed-tangent-hybrid/ESA_DISPATCH_SCOPE_RESULT.md) verifies all 384 accuracy flags and a 1.69–1.72× fit CPU speedup on the two timed full-window comparisons. The wide method remains the reference for the disc and other observed recordings. Independent qualification remains open. |
| L02 | Next | Linear-memory path scoring verified; aircraft law open | [Structured receiver calculations](prediction-observed-development/STRUCTURED_RECEIVER_LIKELIHOOD_RESULT.md) agree with dense results on small controls and a 64,080-report runtime benchmark. The [later-axis scoring check](prediction-observed-development/ESA_STRUCTURED_AXIS_SCORE_RESULT.md) agrees on all 80 saved path comparisons and completes the 4,096-position size check. Qualify the receiver/IMU error law before a longer aircraft fit. |
| E01 | Next | One 20-minute slice verified in every reserved group | The [receiver-only screen](external-imu-data/ESA_CONFIRMATION_RECEIVER_INVENTORY_RESULT.md) found ten provisional windows. [Timestamp integrity](external-imu-data/ESA_CONFIRMATION_TIMING_RESULT.md) passed on the first 20 minutes of the earliest window in each group. The forecast and uncertainty rules still need qualification before confirmation. |
| E02 | In progress | Nearby high-rate reference pending | Using the [same satellite products and aircraft path](prediction-observed-development/ESA_GROUND_COMMON_PRODUCTS_RESULT.md) lowers the measured ground-station disagreement to 1.47 cm RMS. Faster shared errors remain open. The [joint error budget](prediction-observed-development/ESA_REFERENCE_ERROR_BUDGET.md) still needs carrier, anchor and motion limits. The [Nuuk Museum file](prediction-observed-development/ESA_GROUND_REFERENCE_AVAILABILITY.md) requires sign-in. The reserved flights stay closed. |
| G01 | Complete | Raw gyro plot checked; descriptive | The [53-stretch comparison](ilvis0-gyro-companion-v2/INTERPRETATION.md) found median absolute pitch-rate differences of 0.88°/h for the specified-field globe, 2.84°/h for zero-field globe and 5.87°/h for level flat. Aircraft motion and sensor corrections remain mixed into those rates. |
| U01 | Next | Development data and fourteen ground-reference studies verified | The [public snapshots](PAPER_DATASET.md#verify-the-public-evidence) reproduce without original recordings. The NASA table indexes 53 stretches in 27 conservative groups. The ESA table and [ground evidence index](prediction-observed-development/ESA_GROUND_REFERENCE_EVIDENCE.md) account for reused observations within one opened flight. A confirmation dataset awaits qualified uncertainty and independently scored flights. |
| U02 | Next | Simulated calibration passed; aircraft uncertainty open | [Independent simulated validation](prediction-validation-continuation/README.md) verified 4,344 fits across 181 cases, with a 1.64% upper bound on failure under those simulated conditions. The [flight-group count check](PREDICTION_GROUP_COUNT.md) shows why seven reserved ESA groups cannot establish 95% prediction coverage with 95% confidence. The strict [232-file longer-flight inventory](ilvis0-distance-inventory/RESULT.md) found no new recorded date. A separate [receiver/raw scan](ilvis0-receiver-raw-inventory/RESULT.md) found 29 technical candidates on 26 dates, 16 absent from the original selection. Their [receiver-motion profile](ilvis0-receiver-motion-profile/RESULT.md) closed all 29 tasks: 12 tracks fall below both earlier climb and turn reference values, including six new dates. An [alignment-only ablation](ilvis0-alignment-ablation/COMPARISON.md) recovered exactly the original five strict intervals. A [conditional rate-geometry check](ilvis0-receiver-geometry-profile/INTERPRETATION.md) then found that the widest unbounded local nuisance tangent absorbs nearly all three pairwise contrasts on all 29 routes. This does not replace the bounded full-IMU model, but route shape alone cannot qualify the new tracks. Real-aircraft error modeling, full-pipeline information and independent prediction remain the next gates; no significant Earth-model result follows from the simulated bound. |
| U03 | Complete | Generated-data validation passed | A [reboot-resumable continuation](VALIDATION_CONTINUATION.md) completed the original 181-case simulated validation without changing its frozen rule. Its 4,344 fits passed, giving a 1.64% upper failure bound under those simulated conditions; aircraft coverage remains open. |
| R01 | Later | Not started | [Estimate the background rotation vector freely](ROTATION_FIELD.md), rather than supplying its rate. |
| R02 | Later | Waiting for R01 | Test whether the measured rate can distinguish sidereal from solar timing. |
| S01 | Later | Deferred | Develop Wuhan-data analysis and the separate [stationary participant experiment](STATIONARY.md). |
| D01 | Supporting | Ongoing | Seek more instrument documentation. This supports the work without stopping analysis under stated assumptions. |

For V02 and C03, the [curved known-optimum control](prediction-group-transfer/CURVED_BOUNDED_SOLVER_RESULT.md)
passes eight cases each with the current trust-region method and a centered
objective solver. SciPy TRF meets the analytic cost and parameter limits in
all eight cases and fails the unchanged final-position check on six. The
[first generated flight comparison](prediction-group-transfer/CENTERED_FLIGHT_SOLVER_RESULT.md)
then found that the trust region finished in 10 evaluations and the
centered solver reached the study clock limit after 182 attempted
evaluations. The remaining four starts were never charged. The
[saved-derivative scaling test](prediction-group-transfer/SCALED_SOLVER_REPLAY_RESULT.md)
then improved the condition number in all seven controls but qualified
neither version of the centered solver. Keep the existing trust-region
method. The unresolved ESA settings still need a separately qualified
method that handles the coupled calibration directions.
The [curvature-guided retry](prediction-group-transfer/CURVATURE_RETRY_CONTROLS_RESULT.md)
then tried a shorter step along the rejected full direction. Both
methods passed the same four of eight generated cases. The retry
accepted shorter steps on every difficult case and still failed the
final gate. It does not qualify a flight-scale test or a change to
the observed solver.
Adding [residual curvature](prediction-group-transfer/RESIDUAL_CURVATURE_CONTROLS_RESULT.md)
improved the result to five of eight under both tested curvature
methods. Three failed endpoints matched the reported optimal cost,
and the exact generated formula found a positive gap below one
unit of cost precision. Preserve small residual changes at evaluation
before testing another candidate. The fresh gate stays fixed.
The [direct residual change](prediction-group-transfer/DIRECT_RESIDUAL_CHANGE_RESULT.md)
then recovered both curved-interior starts under each curvature method,
raising qualification to six of eight. Both weak-direction starts still
failed. The two recovered comparisons trace to an underestimated step
reduction. The four aircraft failures stay open.
The [strong-residual correction](prediction-group-transfer/STRONG_RESIDUAL_RESTORE_RESULT.md)
then passed all eight cases with analytic curvature, recovering both
weak starts. The finite-difference arm approached both weak solutions
and still passed only six of eight. A practical curvature estimate
and a generated flight-scale test are still needed before any
observed fit can use the method.
The [weak-tangent estimate](prediction-group-transfer/WEAK_TANGENT_CURVATURE_RESULT.md)
then passed all eight generated cases with estimated curvature. A
saved flight-sized tangent has 15 weak directions, which would
require 30 extra calls for one estimate at that point. The next
generated flight check must count those calls and test an available
residual representation.
The [first native flight check](prediction-group-transfer/WEAK_CURVATURE_FLIGHT_RESULT.md)
then hit its 210-second limit after 181 attempted training tangents.
The reference passed in ten. The candidate saved no completed forecast.
The next solver candidate needs a cheaper way to estimate curvature
before a new generated flight can qualify.
The [trial-tangent estimate](prediction-group-transfer/TANGENT_SECANT_CURVATURE_RESULT.md)
passes all eight small controls in 80 evaluations. It reuses
evaluated trial tangents, with no separate probes. Its
[generated flight check](prediction-group-transfer/TANGENT_SECANT_FLIGHT_RESULT.md)
passed its first matched specified-field globe case. The candidate
used 49 evaluations versus ten for the reference, with a largest
withheld path difference of 3.56 micrometres. In the [two remaining
geometry checks](prediction-group-transfer/TANGENT_SECANT_GEOMETRY_RESULT.md),
the disc passed and the zero-field globe stalled after 21 evaluations.
The reference passed on both. A [bounded fallback](prediction-group-transfer/TANGENT_SECANT_FALLBACK_RESULT.md)
preserved the two passes but took 134 attempts on zero-field globe before
reaching its wall limit without a forecast. Keep the established solver
as the reference. The fallback remains unqualified for longer and aircraft
fits. Independent aircraft uncertainty is the priority for validation.

For L01, a [model-declared dispatch](mixed-tangent-hybrid/MODEL_DISPATCH_RESULT.md)
uses the faster arithmetic for the two globe candidates and the established
wide arithmetic for flat. The saved 24-case audit preserves every numerical
disposition. Two generated smoke fits reached matching forecasts but stopped
at an eight-evaluation cap without convergence. A separate
[six-case generated fit study](mixed-tangent-hybrid/dispatched-fit-study/README.md)
then passed all complete paired-fit and prediction gates with a maximum
1.40 × 10⁻⁹ m position difference. The existing long generated timing study
measures a speed gain for the selective tangent. The later observed release
failed its exact-start gate, so the faster method cannot replace the wide
method on aircraft data under this qualification.
The [observed release plan](mixed-tangent-hybrid/OBSERVED_DISPATCH_PLAN.md)
fixed sixteen globe cases and retained eight saved wide flat outcomes. Its
first launch ended on a technical path error before any native call. The
[corrected release](esa-observed-model-dispatch-v2/README.md) sealed all sixteen
fits under 1,240 native calls. An independent saved-only audit verifies the
source, charges and every forecast pair. All 16 pairs pass the fixed 0.01 m
forecast tolerance, but only 5/8 primary training starts agree. The frozen
substitution gate fails; the wide method remains in use. The three start
switches occur at near-tied costs and change forecasts by at most 0.00007914 m,
as detailed in the [saved-fit diagnosis](mixed-tangent-hybrid/README.md).
The eight saved groups include three start switches; their competing-start
training-cost gaps are 1.4×10⁻⁸ to 3.3×10⁻⁴ in the respective objectives.
Those small gaps explain the software sensitivity, but a revised gate chosen
after seeing this flight cannot retroactively qualify the failed release.
Keep the wide method for observed fitting. A new prospective equivalence rule
needs independent generated controls and a separately selected observed
validation input; the seven reserved ESA groups remain protected by the
aircraft-error gate.
The [fresh generated rule check](mixed-tangent-hybrid/START_EQUIVALENCE_V2_RESULT.md)
has passed all six settings. A [saved observed replay](mixed-tangent-hybrid/OBSERVED_START_V2_RETROSPECTIVE.md)
passes 8/8 groups with no absolute cost floor, but is retrospective. The next
L01 gate used a [prospectively frozen development comparison](mixed-tangent-hybrid/OBSERVED_DISPATCH_FRESH_RESULT.md)
on another window. All 16 globe pairs passed. The two
[full-window timing pairs](mixed-tangent-hybrid/ESA_FULL_FIT_TIMING_RESULT.md)
then used 41–42% less fit CPU time with the selective derivatives.
The evidence covers one recording and the tested globe settings.
The flat calculation keeps the established wide derivatives, and
qualification across recordings remains open.

The [saved receiver inventory](prediction-observed-development/ESA_REPEAT_TURN_RESULT.md)
shows five available ranges on recording 187 after removing the four
earlier full supports and the four repeat-turn windows. The first range
that fits the full comparison has receiver support indices **11497–13897**
after leaving a buffer. Taking every other 2 Hz report preserves the
original 1 Hz comparison. The 800 training queries span indices
**11498–13096** and the 400 forecast times span **13098–13896** (all
zero-based and inclusive). Run the metadata-only check with
`env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_dispatch_window`.
The [clock check](mixed-tangent-hybrid/esa-dispatch-clock-result.json)
verified both source hashes, all 2,401 receiver timestamps and 359,730
inertial timestamps. The receiver span was 1,199.99995 s and the largest
inertial timestamp gap was 3.334 ms. Reproduce it by replacing
`lll.esa_dispatch_window` with `lll.esa_dispatch_clock` in the command
above. The check decoded timestamps only. Input preparation and solver
qualification remain open. The solvers can compare their paths at all
400 times without reading the measured forecast positions or using the
reserved flight groups.

The [corrected input preparation](mixed-tangent-hybrid/OBSERVED_DISPATCH_INPUT_V2.md)
closed in 26.7 seconds. It saved 359,729 inertial increments, 800 training
positions and 400 later clock tags. Five focused software checks passed.
The first job's sealed failure came from a JSON selection comparison
and preceded any measurement decoding.

The [paired worker](mixed-tangent-hybrid/OBSERVED_DISPATCH_FRESH_PLAN_V2.md)
keeps all 16 combinations of globe model, processing
assumption, GPS error policy and starting point. Each pair has the
original 200-evaluation limit per fit. Both methods must use the same
training inputs and agree within 1 cm at the later query times. The
primary-start check verifies cost and path agreement across near-tied
starts. Four source-bound software tests passed. The preparation
command checked the saved recovery qualification and staged all 16
pairs after the corrected input job closed. Eighteen focused checks of
the current solver and prediction components passed. The comparison
closed under manifest SHA-256
`9e4f8af256bab5270a216b5d83c97b614a69a1ede6270ec10574fa7caa3c4d1f`.
The [sealed comparison](mixed-tangent-hybrid/OBSERVED_DISPATCH_FRESH_RESULT.md)
passed all 16 pairs and all eight settings. The widest difference among
near-tied predictions was 0.265 mm at the later query timestamps. The
reserved flights and later GPS positions stayed withheld.

A [saved four-model trial audit](ilvis0-measurement-contribution/MATCHED_WIDE_RESULT.md)
found that 559 of 1,238 wider training calls evaluated trial points the solver
never accepted. Forty-nine of 64 wider fits had no such calls. The binary64
count was 1,377 of 2,035. Computing the residual before the derivative at each
trial would exchange 559 derivative calls for 1,046 value-only calls in the
wider trial. That saves time overall if a value-only call costs less than
53% of a derivative call. Check the recorded trial counts and exact residual
equivalence before testing this change on complete fits. The [recorded preflight](ilvis0-measurement-contribution/MATCHED_OBSERVED_NUMERICAL_RESULT.md)
then found one such call across 67 evaluations in the six passing fits,
compared with 18 of 30 in a failed zero-field disc fit. The likely speed
benefit depends on the solver path.

The [saved aircraft point check](ilvis0-measurement-contribution/MATCHED_TRIAL_PROBE_RESULT.md)
reproduced receiver coordinates, residuals and packet-boundary counts exactly
at all four points. Value-only calls used 49–116 times less CPU in these
individual evaluations. The original failed stop remains. Next, qualify an
opt-in trial calculation on full paired fits with identical iteration limits
and verify the residuals, solver decisions, stopping results and forecasts.
The optional solver path now keeps the full tangent at accepted points and in
the fresh stopping check. A known-answer fit reproduced the complete solver
trace with fewer tangent calls. A separate native test verified that each
value and tangent calculation is charged before it runs. The [eight complete
generated comparisons](ilvis0-measurement-contribution/MATCHED_TRIAL_FITS_RESULT.md)
then reproduced all solver records and forecasts exactly, including the
original failed stop. Full tangent calls fell from 290 to 127, with 258
value-only calls. The [equal-limit aircraft check](ilvis0-measurement-contribution/MATCHED_TRIAL_OBSERVED_RESULT.md)
then reproduced both complete IMU8 solver records and the control forecast.
The zero-field disc retained its failed stop and used 12 full tangents
instead of 30. The control saved none. Qualify any broader substitution
on its own recordings and scope.
The [saved ESA work audit](mixed-tangent-hybrid/OBSERVED_TRIAL_WORK_RESULT.md)
finds avoidable derivatives in just one of the 16 sealed pairs. The total
count could fall by 3.1% for wide precision or 8.2% for selective precision
before paying for value-only calls. A timed test is most informative on
fits with many rejected proposals.

To reproduce the audit, open the sealed `ilvis0-matched-wide-v1-20261118`
study with `lll.studies.closed.ClosedStudy`. In each verified `fit.json`, take
the distinct evaluation numbers in `step_history` and subtract the numbers
accepted in any row. Sum by `payload.arithmetic` in the frozen task list.
The manifest SHA-256 is
`e8b2a823364ba888de3e1df8d4b44833d943dc4d71d77bea25f288d2daa66309`.

For E02, the [saved height-error anatomy](prediction-observed-development/CROSS_POINT_HEIGHT_ANATOMY.md)
finds 375–377 consecutive nominal-range misses after the first 23–25 later
reports. Height errors at the two saved calibration settings move almost
together. A [prior local calibration-uncertainty check](prediction-observed-development/LINEAR_UNCERTAINTY_V3_RESULT.md)
improved height coverage only from 25/400 to 26/400 at one setting. The next
generated error-law control must separate changing vertical motion, nonlinear
calibration effects and sensor error; this one-flight diagnostic supplies no
calibrated inflation factor.

For E02, the [saved six-channel check](prediction-observed-development/RECORDED_CHANNEL_DEPENDENCE.md)
finds correlated short-time changes in the recorded gyro and accelerometer;
their physical source and the observed prediction-error law remain unresolved.
An [independent known-motion control](prediction-observed-development/MOTION_ERROR_CONTROL.md)
now supplies analytic aircraft motion and separately known sensor/receiver
errors for testing a candidate method. Its five software checks pass. In one
matched generated example, a naive short-span gyro-noise estimate is 35 times
the known white component; longer spans can miss the physical vibration. This
has not qualified prediction ranges or opened reserved flight groups.
An [analytic control](prediction-observed-development/ERROR_ATTRIBUTION_CONTROL.md)
shows why the sampled channels alone cannot distinguish platform vibration
from correlated sensor error; the next gate must add independent constraints
or qualify an effective prediction-error envelope.
A [withheld-forecast control](prediction-observed-development/FORECAST_AMBIGUITY_CONTROL.md)
shows that identical recorded inputs can yield paths 2.79 m apart after
120 seconds under one illustrative changing-error alternative. It does not
establish an instrument error limit or qualify observed prediction coverage.
An [earlier-origin preflight](prediction-observed-development/ROLLING_ORIGIN_400_PREFLIGHT.md)
verifies a 400-training/120-future cut in the same ESA development recording,
with later receiver positions excluded from fit inputs. Both fit tasks sealed
and passed numerical checks in eight evaluations each, with no active bounds.
The separate [early-only conditioning plan](prediction-observed-development/ROLLING_ORIGIN_400_CONDITIONING_PLAN.md)
passed eight focused checks and five recovery checks. Both tasks sealed with
exact training-prefix replay before the later 120 positions were scored. The
[saved score](prediction-observed-development/ROLLING_ORIGIN_400_CONDITIONAL_RESULT.md)
is 0.56 m horizontal and 0.17 m height RMS after early-only conditioning,
versus 5.38 m raw horizontal RMS. Both error laws agree closely; all nominal
ranges cover the reports but residuals remain strongly correlated. This is
exploratory development, not calibrated coverage, independent confirmation or
a physical adequacy finding over longer periods.
The [matched receiver-only control](prediction-observed-development/ROLLING_ORIGIN_400_RECEIVER_CONTROL.md)
misses by 417–424 m horizontally under two fixed last-minute rules. It tests
those rules against the sealed IMU forecast, not the gyro's separate effect.
The [subsequent reported-velocity control](prediction-observed-development/ROLLING_ORIGIN_400_VELOCITY_CONTROL.md)
misses by 418 m; it was designed after the first result and also holds course
fixed. Neither control qualifies an adaptive receiver-only forecast.
An [earlier-only GNSS velocity audit](prediction-observed-development/GNSS_VELOCITY_CONSISTENCY.md)
finds 0.016/0.007/0.036 m/s RMS differences from position derivatives across
north/east/up, but shared PPP processing prevents treating that agreement as
independent accuracy or a calibrated motion bound.
The [separately frozen 5 Hz motion check](prediction-observed-development/GNSS_5HZ_MOTION_RESULT.md)
uses only the opened flight's 400 earlier report times. GNSS course change and
body-down gyro rate correlate at 0.915 over two seconds and 0.969 over ten
seconds. The changing difference still has 378 and 223°/hour RMS, respectively.
Course is not aircraft heading, so this does not isolate sensor error or
qualify a prediction range. Both technical tasks and the
[portable evidence copy](prediction-observed-development/gnss-5hz-motion-runtime/portable-evidence.zip)
verify; the reserved flights remain closed.
On an idealized known-motion control, the same calculation leaves 1.50 and
1.30°/hour changing difference after declared synthetic sensor errors. The
large recorded differences therefore need a flight-specific motion/error
model; the idealized values are not instrument limits.
An exact [5 Hz aliasing control](prediction-observed-development/OBSERVED_ERROR_PLAN.md)
also leaves receiver position and velocity unchanged between real 10 Hz
vibration and correlated sensor error. The new receiver stream improves motion
context but cannot by itself identify the full error law.
The [earlier-origin development check](prediction-observed-development/ROLLING_ORIGIN_200_INTERPRETATION.md)
now closes a second 120-second forecast in the same opened flight. Both fits
and both conditioning tasks pass. Conditioned horizontal/height RMS is
0.467/0.240 m, versus 0.561/0.169 m at the prior origin. The two laws are
nearly identical; all nominal ranges cover, but adjacent errors are strongly
correlated. This supports temporal transfer within one flight, **not** an
independent coverage rate. Further overlapping origins are low value; the
next gate is a generated, motion- and drift-aware error range fixed before
the seven reserved ESA flight groups are scored.
The [training-only covariance audit](prediction-observed-development/GNSS_COVARIANCE_AUDIT.md)
matches all 400 earlier reports to the verified original GNSS export. None
of its printed position or velocity matrices has a negative eigenvalue,
but the shared PPP solution and missing cross-time/cross-field covariance
prevent turning these fields into an observed motion-error law.
The [parallel receiver check](prediction-observed-development/PARALLEL_GNSS_RESULT.md)
matches both other PPP exports at all 400 earlier times. Their centimetre
differences provide a hardware cross-check, while shared antenna and possible
processing errors leave absolute accuracy and the full error law open.
A [common-time follow-up](prediction-observed-development/PARALLEL_GNSS_TIME_RESULT.md)
reduces the east-axis RMS differences after accounting for submillisecond
offsets with reported velocity; it remains an exploratory relative check.
A [saved-fit cross-check](prediction-observed-development/PARALLEL_GNSS_FIT_RESULT.md)
compares both unchanged fitted trajectories with all three receivers on 400
training epochs. The raw trajectories miss each stream by about 0.8 m north
and 1.0 m east RMS. Receiver-specific disagreement is much smaller, but
common errors and model mismatch remain unresolved. The later conditioned
forecast is a separate calculation.
That [sealed conditioned forecast](prediction-observed-development/PARALLEL_GNSS_FORECAST_RESULT.md)
scores similarly against all three receivers on the 120 later epochs:
0.554–0.563 m horizontal and 0.169–0.197 m height RMS. It is a post hoc
same-flight hardware check, not independent validation or error-law coverage.
The [GPS-only constant-turn follow-up](prediction-observed-development/ROLLING_ORIGIN_400_TURN_CONTROL.md)
fits course rate on the last 60 earlier receiver velocities. It misses the
same later 120 reports by 448 m horizontally, versus 418 m for the
fixed-course control. This development comparison does not isolate the gyro
or qualify the forecast error law.
The next gate remains a defensible motion/IMU/receiver error range and
prediction check on a separately selected recording.

For C04, a [joint force-magnitude covariance helper](ilvis0-measurement-contribution/CHANNEL_CONTROLS.md)
now passes eight checks. It propagates a supplied GPS-position
covariance through overlapping gyro-free force estimates. The actual receiver
error law, nonlinear coverage and complete matched channel comparison remain
open.
The [saved paired-gyro time-scale check](ilvis0-pair-rate-scale/RESULT.md)
verifies twelve overlapping recorder pairs. Median X/Y/Z differential RMS
falls from 5.47/10.05/2.37°/h at one second to 0.11/0.47/0.16°/h at one
minute. Differential mounting, timing and processing remain possible, so
these numbers cannot yet become a sensor-noise prior.
An [earlier-only relative-alignment check](ilvis0-pair-alignment/RESULT.md)
reduces later-half disagreement in 11 of 12 pairs, but leaves a 12.26°/h
median per-second vector RMS after rotation and offset. The fixed one-minute
window median is 0.31°/h. It does not identify intrinsic noise or transfer an
error law to ESA.
The [whole-packet timing check](ilvis0-measurement-contribution/PAIRED_GYRO_CLOCK_RESULT.md)
now finds that one-sample timing shifts change later short-window disagreement
by less than 5% on two known overlaps. The mixed pair changes its preferred sign
with window length. A single delay leaves most relative gyro error unexplained.
The timed-GGA receiver-only bridge passes five further checks: all models use
the same selected windows, and receiver error remains shared across windows
and physical candidates.
No recorded flight has been fitted by this bridge.
The earlier dense bridge's 128-epoch limit and conditional window selection are explicit
remaining gates before a whole-stretch contribution comparison.
A separate structured projection passes six checks against the dense reference
and supports 2,000 receiver epochs without a dense epoch covariance. Four
further checks connect it to common GPS-selected windows, including a 200-fix
history. Calibrating receiver error, accounting for selection uncertainty and
connecting this statistical covariance path to the existing matched
acceleration observations remain open.
Recorded use must split receiver blocks at gaps above the declared limit;
the current bridge rejects such a block rather than filling missing fixes.
The [sealed receiver-gap inventory](ilvis0-receiver-gap-inventory/README.md)
checked all 53 preselected stretches without refitting: 52 saved primary-receiver
streams each form one uninterrupted block under the 1.5-second rule, and one
retains its prior decoder failure. Original row ranges and all dispositions
are public. This settles receiver completeness for these saved streams, while
receiver-error calibration and matched IMU-channel attribution remain open.
The structured bridge now accepts those enhanced-position record fields under
their own source label; 34 focused new/existing checks pass. Its first recorded
matched IMU use must freeze a receiver-error law and support policy before inspecting IMU
model residuals.
The [frozen receiver-only window study](ilvis0-receiver-support-inventory/README.md)
has now applied one such policy to the 53 preselected stretches: 2,194 of
2,365 targets are supported, with the prior decoder failure retained. This
qualifies neither the supplied receiver-error law nor selection uncertainty;
a matched recorded IMU-channel analysis remains gated on those checks.
The [saved window-margin audit](ilvis0-receiver-support-inventory/MARGIN_AUDIT.md)
preserves all 7,095 candidate spans and finds 398 chosen windows within
0.10 m/s of the fixed vertical-motion limit. It quantifies closeness to that
one threshold; receiver-error and full selection stability remain open.
The [eleven-pair receiver check](ilvis0-receiver-window-pairs/README.md)
applied the same screen at 490 common times: both receivers accepted 456,
both rejected 27, and seven decisions differed. This measures relative
repeatability; absolute receiver error and matched IMU-channel attribution
remain open.
The [saved window-stability check](ilvis0-measurement-contribution/WINDOW_STABILITY_RESULT.md)
certifies 1,580 of 2,194 chosen windows unchanged under hypothetical
±0.05 m/s speed/climb and ±0.05° course errors; under ±0.10 m/s and the same
course range, it certifies 1,111. Uncertified choices are not observed flips.
These bounds expose selection sensitivity but do not calibrate absolute GPS
error, perturb positions or resolve the matched IMU-channel gate.

For L01, the [saved-fit failure diagnostic](esa-observed-hybrid/FAILURE_DIAGNOSTIC.md)
measures all three failed ESA pairs without refitting. It narrows the next
method-development check to derivatives evaluated at identical saved points.
The [finite same-point result](esa-observed-hybrid/same-point-result/README.md)
completed all twelve charged native evaluations and independently replayed the
saved arrays. Values and boundary counts agree at all six saved points;
derivative differences reach about 0.0000012 m per normalized parameter unit.
The [revised six-point check](esa-observed-hybrid/same-point-v2/README.md)
passes all six predeclared derivative-improvement gates without refitting.
The faster method remains unqualified for observed substitution, so the
established wide tangent stays in use. The [finite three-pair check](esa-observed-hybrid/three-pair-v2/WALL_CAP.md)
reached its four-hour cap with 0/3 comparisons completed. All three tasks
sealed budget failures after 349 charged native calls; two saved wide fits
passed numerical stopping and one did not. These are hash-checked partial
results. The qualified unfinished-task recovery
route does not apply to these completed budget failures. Any further method
work needs a distinct, prospectively qualified design; it cannot relabel or
retry these results.
C03/V02 real-recording error adequacy is the higher-priority gate.
The new seven-check law-family helper unions matched affine forecast intervals
across supplied error assumptions without choosing a law by training score.
This preserves a known mathematical guarantee only if one supplied Gaussian
law is correct and its calibration box contains truth. It does not calibrate
aircraft prediction coverage or unblock the observed-data adequacy gate.

The [saved ESA error-dependence audit](esa-prediction-error-scale/CORRELATION.md)
now verifies all 22 available forecasts from development recording 187.
Successive forecast errors, about one second apart, remain strongly correlated
after linear detrending;
the 400 later epochs per fit are not independent validation cases. The audit
also finds later errors 84–178 times the fitted earlier residual RMS by axis
for the specified-field globe. Training fit residuals cannot supply a fixed
future error scale on this recording. The
[separate NASA development pilot](ilvis0-retrospective-prediction-pilot-v2/ERROR_STRUCTURE.md)
shows 13–47-fold growth by axis among its nine numerically qualified
specified-field settings. Its saved one-second errors also rise across the
four withheld quarters, especially in height. Neither audit estimates a usable error law or
touches reserved confirmation groups.
The [completed rolling-origin study](prediction-rolling-origin/INTERPRETATION.md)
tests whether error observed before the original withheld period transfers to
an equal-length later forecast. Its 43 source-bound method checks and six
publication checks pass. The separately frozen 48-start NASA development run
returned all tasks: 34 numerically pass, 14 do not, and eight of twelve
clock/processing settings have qualified fits at both cuts. North error ratios
range from 0.44× to 4.09× across these repeated settings; no single future
uncertainty multiplier is calibrated. The historical pilot's source and
results remain preserved.
Four [additional conservative NASA development groups](prediction-group-transfer/README.md)
were fixed using route, IMU type and provenance metadata only. Their
[transfer plan](prediction-group-transfer/OBSERVED_PLAN.md) fixed an
earlier-only empirical error reference and a sixteen-start grid. The
[verified result](prediction-group-transfer/RESULT.md) sealed all 16 fits
under 611 native calls: six passed numerical checks, and three of four
groups have scorable second-cut forecasts. All three meet the descriptive
reference and separate physical screen; one group abstains. This does not
calibrate observed-aircraft coverage or Earth-model significance.
The [saved stopping-probe replay](prediction-group-transfer/STOPPING_DIAGNOSTIC.md)
finds that seven of ten nonpassing fits miss only the original cost-change
check; two miss cost and stationarity, and one stops before the full probe.
The original failures remain unchanged. This directs later numerical-method
work without treating near agreement as convergence.

For C03, an [independent linear known-answer control](PREDICTION_ERROR_LAW_PLAN.md)
checks separate gyro, accelerometer and receiver noise streams. The
observed-input adapter now passes a short matched two-law native control and
binds the saved ESA development interval without reading later receiver rows.
The no-fit covariance constructor passes short native controls for both
prediction targets. The [real-size source-bound preflight](prediction-observed-law-preflight/RESULT.md)
passed all four technical tasks on the selected ESA development recording,
using both supplied laws and both prediction targets. The first frozen attempt
failed before native work on an input-key check and remains sealed; the
corrected run completed under its own allowance. This qualifies operator
construction and the withheld-data boundary, not observed error coverage.
The [separately frozen finite development fit](prediction-observed-development/DIAGNOSIS.md)
sealed a technical failure at its 3,000,000 native-call allowance. Both laws'
fits converged and both forecasts were saved, but the second
receiver-measurement bound was unfinished. The withheld receiver observations
were not opened. A separate continuation must qualify saved-artifact reuse,
the missing bound, a new finite allowance and recovery before any observed
score. The original failure remains preserved. The
saved-artifact binder and no-fit forecast guard pass seven software checks.
The [generated native check](prediction-observed-development/CONTINUATION_PLAN.md)
reproduced the sealed missing receiver bound, diagnostic, both law unions and
withheld score exactly without refitting. Generated withheld positions were
opened only after both unions. The frozen continuation worker passed its
1/1 generated task with an exact sealed-control match. Task-level recovery
passed seven finite interruption checks. The separate
[recording-187 continuation](prediction-observed-development/CONTINUATION_RESULT.md)
completed 1/1 task and scored 400 withheld receiver positions. Both saved
forecasts fail the preset horizontal accuracy limits, including about
249 m RMS later error. The assumed-law intervals contain the later receiver
readings, but the law is uncalibrated and the scientific decision is abstain.
A saved-only reporter verified the result without refitting. The
[saved error-trend audit](prediction-observed-development/DRIFT_AUDIT.md)
finds an east-error trend of about −23.6 m/min in the final two minutes of
training, steepening to −41.6 m/min during the withheld period. The two
error laws behave almost identically. The saved native training differences
and forecast positions agree within
0.000000001 m, so saved-forecast handoff is not the source of the 40 m
training error. Its source remains undetermined. The next step is to explain
the inadequate training fit with motion, timing and calibration controls on
known-answer data before further observed fitting. The
[fixed GPS-only reference](prediction-observed-development/RECEIVER_REFERENCE_RESULT.md)
uses the same development split and scores 535 m local-linear and 572 m
spherical constant-course horizontal RMS later error. The saved IMU forecast
is closer at about 249 m, but remains physically inadequate; neither
comparison isolates the gyro or calibrates an Earth-model decision. The
[sealed generated-error comparison](prediction-observed-development/TRAINING_ADEQUACY_COMPARISON.md)
finds 2.25–3.19 m training horizontal RMS across 24 noisy known-answer
cases, versus about 40 m in the recorded development case. All 24 generated
cases also fail their later accuracy screen. Existing synthetic noise
assumptions do not explain the recorded training miss; recorded rate,
timing and motion interpretation are the next checks. The
[finite identification trial](prediction-known-answer-identification/RESULT.md)
completed 400 generated histories: 166 provisional single-law choices,
234 abstentions and five wrong choices. The true supplied law covered
3,764/4,000 later receiver epochs at the nominal 95% level. This tests a
small fixed-law family; full aircraft prediction and observed error adequacy
remain open.

The [paired aircraft error-law study](prediction-paired-law/RESULT.md) verifies
12 two-minute recordings and 24 matched fits, all passing numerical and
physical prediction screens. The training minimum matches the generating IMU
law in 6/12 comparisons, with no training-score separation above 0.000083.
The largest future scale ratio is 1.0000023; these cadence-matched laws are
nearly equivalent for the receiver forecasts in this two-minute study.
Calibration bounds are active in every comparison;
fixed-parameter 95% marginal coverage is 1,924/2,880 for physical position
and 2,242/2,880 for future receiver reports. These counts do not establish
coverage after fitting. All scientific decisions abstain. Bound-aware
nonlinear uncertainty and independent-seed coverage tests precede any observed
aircraft error-law claim. The [saved ESA timing check](prediction-paired-law/SAMPLING.md)
finds a 1.00000469 accumulated white-noise variance ratio across 239,863
earlier packet intervals, so timing variation in this development interval
does not justify a longer same-cadence law-identification campaign.
The [bound-aware affine control](bounded-calibration-prediction/README.md)
passes nine local tests, including an active-limit Monte Carlo check, an
unidentified-direction case and an independent dense check of its aircraft
forecast adapter. Its 95% marginal guarantee assumes a known Gaussian law
and an affine model. The first [nonlinear generated-aircraft release](bounded-calibration-prediction/NONLINEAR_RESULT.md)
closed 24/24 technical cases with 23/24 combined numerical and accuracy passes.
Its complete interval containment is a development observation, not a
calibrated coverage guarantee. The [saved eight-point probe](bounded-calibration-prediction/TIMING_PROBE_RESULT.md)
rules out packet switching alone as the explanation for the one failed
stopping case, while preserving its terminal technical wrapper and the
original 23/24 result. Coupled calibration/timing behavior remains open.
The separate [two-seed method check](bounded-calibration-prediction/INDEPENDENT_SEEDS_RESULT.md)
passes 48/48 combined numerical and withheld-position screens, but its two
draws per condition do not establish 95% coverage.
A paired-law adapter now saves the union of two bounded marginal
forecast intervals before generated later truth is opened. It preserves
active calibration bounds, binds each interval to its target error operator,
and abstains if either fit is unqualified; eight software checks pass. Fresh
native two-fit controls pass for both generating laws and both calibration
cases on short generated recordings. The
[finite generated-aircraft study](prediction-paired-bound-family/RESULT.md)
now verifies all 24 recordings and 48 matched fits across the original
allowance and a separate four-recording continuation; no
observed-aircraft error law is calibrated by this software check.
Its eight-check saved-result audit independently replayed every withheld score.
Both target intervals contain all later coordinates in 24/24 generated
recordings. The recording, rather than each correlated epoch, is the unit of
the descriptive tally; 95% coverage is not established by this matrix.
The first [whole-period study](prediction-simultaneous-law-family/RESULT.md)
sealed 96/96 package-import failures before any numerical work. It yields no
coverage evidence. A [new independently seeded cohort](prediction-simultaneous-law-family-v2/RESULT.md)
passed a frozen-worker preflight and closed 96/96 tasks across its original
allowance and a qualified continuation of 12 unstarted tasks. Ninety-two
recordings yielded complete paired forecasts; both target intervals contained
every later coordinate in those recordings. Four original tasks stopped at
the eight-hour cap and count as failures. The exact one-sided 95% upper
failure bound is 9.28%, so the declared 5% gate failed. The
[separate 96-recording cohort](prediction-simultaneous-law-family-v3/RESULT.md)
closed under its qualified continuation. Ninety-five recordings passed both
fits and both withheld targets; one failed numerical stopping and counts as a
failure. The exact one-sided 95% upper failure bound is 4.85%, passing the
frozen 5% gate for that generated mixture. This does not establish observed
aircraft coverage.
No failed or completed task is eligible for an unchanged retry.
A separate five-check affine control also derives a conditional bound for an
entire withheld stretch by allowing for all future coordinates at once. It
remains a mathematical control until nonlinear and observed-aircraft coverage
are qualified in a separate study. Four further checks connect the bound to
both aircraft forecast targets and preserve each target's error-operator
binding through the two-law union. A separate short native generated-aircraft
fit also saves both target intervals before opening later observations. The
two-law union rejects mismatched future time grids; twelve focused checks pass.
This does not establish nonlinear or observed-aircraft coverage.

## Development record

The studies below explain how the current phase was reached. The active tasks
and their gates are in the backlog above. Preserve these completed and failed
results; their old allowances do not authorize rerunning them.

1. Preserve the qualified software controls and completed archival pilot, including
   its numerical and accuracy failures. Broader prediction validation remains open;
   ranges across starts are not calibrated confidence intervals.
2. Preserve the completed ESA comparisons and their failures. The
   [height-gravity revision](esa-observed-height-pilot/README.md) improves the
   matched prediction and completes one adequate three-model setting. Diagnose
   its stopping failures using the [completed fit-free resolution probe](esa-stopping-resolution/README.md).
   The [precision comparison](esa-precision-diagnostic/README.md) completes all
   24 cases: extended integration precision brings all eight field-globe cost
   changes below the existing limit. This diagnoses precision sensitivity at the
   saved points; it does not qualify a revised solver or accept failed fits.
   All [48 long known-motion controls](esa-wide-tangent-controls/README.md) now pass.
   The [matched training study](esa-wide-training-controls/README.md) now
   qualifies all 24 cases, using 268 calls in 113.96 minutes. The
   [observed precision revision](esa-observed-wide-pilot/INTERPRETATION.md) now
   completes three adequate matched comparisons after 56 source-bound checks.
   It preserves all 24 outcomes: 22 numerical passes and two deadline-limited
   starts. The [saved-error check](esa-error-structure/INTERPRETATION.md) now
   verifies all 22 curves without refitting. Errors and their changes remain
   strongly correlated; a receiver-only error assumption is not a complete
   prediction-error law. The [known-noise study](esa-noisy-prediction/README.md)
   completes all 24 fits numerically, but none meets the unchanged physical
   accuracy screen. Later horizontal RMS is 83.6–88.6 m. The
   [verified interpretation](esa-noisy-prediction/INTERPRETATION.md) preserves
   all failures; broader prediction tests remain gated on the revised error model.
   The [training-only rate diagnostic](esa-training-rate-variation/README.md)
   now verifies six-channel variation over 13.33 minutes without fitting. Its
   dependence on sample spacing means that aircraft motion and processing must
   remain distinct from a white sensor-noise assumption. No stress-test setting
   or accuracy limit is changed by this descriptive check.
   The [checked error-budget example](esa-noisy-prediction/ERROR_BUDGET.md)
   also shows why gyro uncertainty accumulates into correlated position errors.
   A revised stochastic prediction-error model needs its own qualification;
   choosing a larger error allowance merely to pass is not a substitute.
   The [shared covariance component](integrated-noise-covariance/README.md)
   now passes 54 software checks, including conditioning across the training
   boundary, stationary changing bias and shared query/endpoint errors. The
   [Native state/input derivatives](native-noise-linearization/README.md) now
   pass 18 source-bound checks across all twelve candidate/processing/gravity
   combinations. Their [complete-history extension](native-noise-linearization/HISTORY_PLAN.md)
   now passes 38 source-bound checks: all twelve longer generated cases preserve
   the nominal positions, and short histories agree with independent nonlinear
   noise perturbations. A separate [receiver extension](integrated-noise-covariance/RECEIVER_PLAN.md)
   passes 15 source-bound checks for offsets, drift, persistent errors and
   earlier-only prediction. Their [combined path](native-noise-linearization/COMBINED_PLAN.md)
   passes twelve native checks with every active calibration column retained.
   The [linear calibration extension](integrated-noise-covariance/CALIBRATION_PLAN.md)
   passes 15 checks and abstains when an unknown calibration direction changes
   the forecast. The separate [ESA rate-point law](integrated-noise-covariance/POINT_PLAN.md)
   passes 15 checks, preserving shared samples between neighboring intervals.
   Its [native adapter](native-noise-linearization/README.md) now passes 65
   checks within a 182-check source-bound suite, retaining both input laws and
   the full 33-state receiver combination. The
   [training-only native adapter](integrated-noise-covariance/training-adapter-qualification/README.md)
   now passes 56 checks. A separate [112-check accounting gate](integrated-noise-covariance/prepaid-native-qualification/README.md)
   permits bounded native blocks without per-packet durable transactions.
   The [sampled-rate error generator](integrated-noise-covariance/rate-point-input-qualification/README.md)
   also passes 54 checks. The [short native protocol](integrated-noise-covariance/short-native-protocol-qualification/README.md)
   now passes 128 software checks. Its two-second cases retain numerical
   nonconvergence and unidentified calibration; they do not qualify longer
   prediction. The [verified two-minute study](structured-noisy-training/README.md)
   now returns all 24 forecasts within the physical screen; 20 pass numerical
   checks. Horizontal RMS is 1.84–2.08 m and height RMS 0.17–0.25 m. Every
   calibration reaches at least one bound, preventing unrestricted uncertainty
   claims. The [saved-data diagnosis](structured-noisy-diagnosis/INTERPRETATION.md)
   now finds strongly coupled gravity/accelerometer columns; the four stopping
   failures miss only cost stability, not their evaluation budgets. The
   [bounded-error adapter](integrated-noise-covariance/bounded-state-qualification/README.md)
   passes 58 checks, its native protocol 69, and the [native connection](integrated-noise-covariance/native-bounded-reference-qualification/README.md)
   all 24 controls. The original 22/24 failure is preserved: an [exact-arithmetic
   diagnosis](integrated-noise-covariance/native-bounded-numerics/README.md) identified
   the dense reference's whitening solve. Nonlinear approximation limits and
   coverage remain before more fits. This shorter study does not supersede the original
   twenty-minute failure. Nonlinear coverage remains open before new aircraft fits.
   Accuracy limits, input selection and calibration bounds remain unchanged.
   The [known-calibration benchmark](noisy-prediction-benchmark/README.md)
   completed all four fixed settings after 27 construction and 14 lifecycle
   checks. With calibration and starting state supplied, the calculated horizontal
   error scale grows from 0.52 m at two minutes to 33.77 m at twenty minutes.
   The longer setting exceeds the unchanged 10 m screen even with this extra
   knowledge. These are assumed-noise calculations, not measured aircraft errors;
   they help explain why longer prediction needs an explicit uncertainty budget.
   The [matched nonlinear check](noise-nonlinearity/README.md) is complete:
   both short settings pass; both longer settings fail the fixed finite test.
   Four of 64 seed/settings controls miss the limit, all in height. The
   [saved diagnosis](noise-nonlinearity/remainder-diagnosis/README.md) locates
   small, closely quadratic effects: largest vertical departures are 7.3 cm
   and 4.4 cm. This supports the covariance calculation as an error-scale
   diagnostic, while preserving its failed strict approximation checks.
   Do not refine those small effects merely to obtain a pass. The next task is
   qualification of the complete fitting-and-uncertainty procedure with unknown
   calibration, separating numerical completion, physical accuracy and coverage.
   Its [saved scoring gate](fitted-prediction-scores/INTERPRETATION.md) is now
   complete: all 24 starts are retained, with 20 numerical passes and ten
   training-selected comparisons available. Their maximum error/noise scores
   are 5.29–6.25; those ratios are not confidence levels. New independent
   calibration/validation draws require their own qualified finite freeze; the
   existing shared seed cannot establish coverage. First [separate draw identity
   from covariance assumptions](prediction-score-qualification/INDEPENDENT_DRAWS.md).
   That interface now passes [30 compatibility checks](prediction-score-qualification/draw-qualification/README.md),
   including identical original-seed outputs against the frozen generator.
   The [fresh-draw pilot](independent-noisy-training-pilot/INTERPRETATION.md) is
   complete: all 48 fits pass numerical and position-error checks. A 17-check
   saved-results audit verifies the new outcomes and reproduces the earlier
   report unchanged. Every selected fit reaches a calibration bound. Their
   error/noise scores are 7.50–11.22 when fitted calibration is treated as known;
   the next step must include its uncertainty rather than enlarge a threshold
   from these two seeds. Neither coverage nor a rare-tail quantile is established.
   The [independent-draw ledger](prediction-score-qualification/calibration-targets-qualification/README.md)
   now passes 30 source-bound checks, including distinct calibration and
   validation targets. It preserves unavailable predictions and rejects
   overlapping draw roles. The [execution design](prediction-score-qualification/EXECUTION_PLAN.md)
   fixes a generated population and separate finite phase allowances, with
   cooperative early stopping if success becomes impossible. Its
   interfaces are now qualified by 62 source-bound checks. The
   [calibration phase](prediction-calibration/README.md) stopped under its
   predeclared futility rule after both starts failed one required setting.
   The [bounded review](prediction-phase-review/README.md) is complete.
   The [four-point diagnostic](prediction-stopping-consistency/INTERPRETATION.md)
   also completes: repeatability is exact, but its derivative comparisons disagree.
   The [small timing controls](timing-precision-controls/INTERPRETATION.md) then
   reproduce packet-boundary slopes and loss of weak coordinate changes.
   Their [matched follow-up](saved-point-timing-arithmetic/INTERPRETATION.md)
   explains the timing discrepancy but leaves gyro-offset comparisons outside
   the fixed scale. No finite threshold or validation result is available.
   The [coordinate controls](coordinate-precision-controls/INTERPRETATION.md)
   pass all six compensated cases. The subsequent [full saved-point check](saved-point-coordinate-precision/INTERPRETATION.md)
   passes all 315 derivative comparisons and all four original stopping probes;
   later solver qualifications and their failures are recorded above.
3. Test broader predictive accuracy before opening the reserved ESA flight groups.
   The [fixed metadata plan](esa-broader-development/README.md) selects the first
   and last twenty minutes of each eligible development run: four ranges, one
   already analyzed and three additional candidates. They share one group and
   require separate preparation and fitting gates. Confirmation groups remain
   untouched until selection, method and decision rules are fixed.
4. Establish confidence at the flight-group level. Then pursue the free rotation
   rate and solar-versus-sidereal studies.

Completed studies remain unchanged. A failed check blocks the work that depends
on it; it does not restart earlier studies or create extra attempts.

Study orchestration and evidence storage use the [shared reproducibility
interface](REPRODUCIBILITY.md). Historical code and evidence retain their original
bytes inside verified archives; storage changes do not alter qualification.

[Plain-language next steps](NEXT_STEPS.md) ·
[Technical requirements and supporting evidence](ANALYSIS_DETAILS.md) ·
[Completed studies](STUDIES.md).
