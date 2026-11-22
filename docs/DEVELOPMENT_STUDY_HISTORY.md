# Archived next steps

This page preserves the earlier research record. Statements about what comes next reflect those study stages. See the [current page](NEXT_STEPS.md) for the active status and plan.

# What comes next

The globe with a specified background angular field fits all 53 selected
aircraft stretches better than either zero-field alternative. When both
geometries are tested with zero field, the disc has the lower cost on 18
stretches under both tested processing assumptions. The 53 stretches belong
to 27 groups that account for overlap between recordings. The result
compares specified physical models on the archive. The accuracy of forecasts
on independent flights and the strength of evidence across flights still
need validation. [Current findings](CURRENT_STATUS.md)

Holding the field at zero gives lower globe costs on every stretch in
17 groups, lower disc costs on every stretch in five, and both outcomes
in the remaining five. [Zero-field results by recording group](analysis-provenance/NASA_ZERO_FIELD_BY_GROUP.md)

One IMU21 recording now has all four withheld forecasts. Globe has
lower total position error at both matched fields. At zero field the
disc has lower height error. Both results survive the measured GPS spread.
[Four-candidate check](ilvis0-measurement-contribution/MATCHED_UNSTARTED_DISC_RECOVERY_RESULT.md) ·
[Receiver sensitivity](ilvis0-measurement-contribution/MATCHED_IMU21_RECEIVER_HULL_RESULT.md)

The [four-flight audit](ilvis0-measurement-contribution/MATCHED_FOUR_GROUP_AUDIT_RESULT.md)
verifies 15 of 16 held-back forecasts across the selected groups. The
specified-field globe meets the fixed accuracy limits on three flights.
Globe has lower total error in all completed same-field comparisons.

The [paired accelerometer study](ilvis0-measurement-contribution/PAIRED_ACCELEROMETER_RESULT.md)
shows how two recorders on the same aircraft agree as their data are averaged.
One pair agrees much more closely than the other. Absolute sensor accuracy
and motion within individual packets still need separate checks.
On the same two flight groups, the [full gain-range check](ilvis0-measurement-contribution/FORCE_GAIN_RANGE_RESULT.md)
shows why the acceleration-only screen leaves all four candidates open.
The [same-window comparison](ilvis0-measurement-contribution/PAIRED_FORCE_WINDOW_RESULT.md)
finds that uncertainty where packets cross the window edges is too large to
check the needed accelerometer accuracy.

An inertial measurement unit (IMU) uses gyroscopes to record angular motion
and accelerometers to record specific force. The flight analysis combines
those measurements with positions reported by a separate GPS receiver.
The method accounts for the receiver's geographic coordinate system.
[How the study works](METHODOLOGY.md)

## Current development work

Both solvers agreed on all 16 matched pairs on one ESA development
window. At nearby starting points that fit equally well, their forecasts
differed by less than 0.27 mm. [Solver comparison](mixed-tangent-hybrid/OBSERVED_DISPATCH_FRESH_RESULT.md)
Short recorded fits ran 2.19–2.84× faster in CPU time. The two full-window
comparisons ran 1.69–1.72× faster and met the same numerical agreement checks.
[Full-window timing study](mixed-tangent-hybrid/ESA_FULL_FIT_TIMING_RESULT.md)
A check of the saved solver records found a way to skip full derivative
calculations in just one pair. The payoff depends on how often a fit
rejects a proposed step. [Solver work audit](mixed-tangent-hybrid/OBSERVED_TRIAL_WORK_RESULT.md)
On eight generated NASA-style fits, skipping repeated evaluations saved
15% of training calls and preserved every fit outcome and forecast.
Two recorded-aircraft controls gave exactly the same forecasts and used
the same number of evaluations.
[Generated comparison](ilvis0-measurement-contribution/MATCHED_REUSE_GENERATED_RESULT.md) ·
[Recorded comparison](ilvis0-measurement-contribution/MATCHED_REUSE_OBSERVED_RESULT.md)

A [shorter solver step](prediction-group-transfer/CURVATURE_RETRY_CONTROLS_RESULT.md)
did not improve the generated qualification. Both methods passed four
of eight cases. The four difficult aircraft fits remain open.
[Using residual curvature](prediction-group-transfer/RESIDUAL_CURVATURE_CONTROLS_RESULT.md)
raised the generated result to five of eight. Some costs rounded
to the known optimum while fresh stationarity still failed.
[Direct residual changes](prediction-group-transfer/DIRECT_RESIDUAL_CHANGE_RESULT.md)
raised the generated result to six of eight. Both weak-direction
starts still failed.
[Correcting the strongly constrained residual](prediction-group-transfer/STRONG_RESIDUAL_RESTORE_RESULT.md)
then passed all eight when exact curvature was available. The estimated
curvature version still passed six. The harder weak-direction cases
must pass with a practical curvature estimate before testing it on a
generated flight.
The [weak-direction estimate](prediction-group-transfer/WEAK_TANGENT_CURVATURE_RESULT.md)
now passes all eight small controls. It still needs a generated
flight test to check the cost of the derivative probes and the
accuracy of the final forecast.
The [first generated flight run](prediction-group-transfer/WEAK_CURVATURE_FLIGHT_RESULT.md)
hit its time limit before saving a forecast. Its reference finished
in ten evaluations. A practical solver needs fewer derivative calls.
The [trial-tangent method](prediction-group-transfer/TANGENT_SECANT_FLIGHT_RESULT.md)
then passed the same generated case in 49 calls, with no separate
derivative probes. The [next matched tests](prediction-group-transfer/TANGENT_SECANT_GEOMETRY_RESULT.md)
passed for the generated disc. The zero-field globe stopped while its fit
could still improve. A [bounded fallback](prediction-group-transfer/TANGENT_SECANT_FALLBACK_RESULT.md)
then reached the time limit on that same case. The established solver stays
in use. Independent aircraft prediction accuracy remains the priority.

An earlier GPS error correction improved later height in all seven
additional NASA groups tested. The same correction increased height
error in all six cases on the ESA development flight.
[NASA check](prediction-group-transfer/HEIGHT_TRANSFER_RESULT.md) ·
[ESA check](prediction-observed-development/ESA_HEIGHT_ERROR_TRANSFER_RESULT.md)

On the ESA development flight, error allowances that fit one part of the
flight often miss another. The latest test fit six windows at a time. Only
three of eight omitted windows met the error reference, and the overall
score worsened. The hardest turn shows disagreement in all three directions.
The aircraft uncertainty rule still needs to work on unused data before the
seven reserved flights can be evaluated.
[Latest transfer test](prediction-observed-development/ESA_SCALE_REFERENCE_TRANSFER_RESULT.md) ·
[Error checks and remaining gaps](ESA_ERROR_POLICY.md#from-development-comparisons-to-an-independent-flight-test)

On the saved ESA forecast pair, the best linear comparison can tolerate
2.25 cm of independent position error. If velocity errors act alone,
the same comparison allows 4.69 mm/s per axis. Four full integrations
changed the score very little. We still need to establish how far the
score can move across all allowed calibrations.
[Forecast margin check](prediction-observed-development/ESA_COMPACT_FORECAST_MARGIN_RESULT.md) ·
[Accumulated velocity errors](prediction-observed-development/ESA_INTEGRATED_CONTRAST_SUPPORT_RESULT.md) ·
[Full integration check](prediction-observed-development/ESA_CONTRAST_REPLAY_RESULT.md)

On the same flight, replacing the GPS position path with one from GPS
or GLONASS velocities shifts the fixed shape score by 31.5% or 25.8%
of its gap. These comparisons leave shared aircraft measurement errors
unbounded. [In-flight Doppler check](prediction-observed-development/ESA_DOPPLER_CONTRAST_RESULT.md)
An error shared across all paths could move the score by its full gap
while matching position and velocity at both ends. The worked example
reaches 0.71 m of north-axis error in between.
[Shared-motion check](prediction-observed-development/ESA_SHARED_MOTION_GAP_RESULT.md)
The recorded satellite clock change is too small and follows a different
pattern. [Carrier comparison](prediction-observed-development/ESA_SHARED_MOTION_CARRIER_RESULT.md)

A [timing check](prediction-observed-development/ESA_FORECAST_TIME_SHIFT_RESULT.md)
tried shifting each saved path slightly forward or backward. Learning the
shift from other windows left seven of eight outside the error reference.

Allowing errors to [persist after turns](prediction-observed-development/ESA_INNOVATION_PERSISTENCE_RESULT.md)
improved the score on all eight windows. Two met the fixed error reference.
[Estimating size and persistence together](prediction-observed-development/ESA_JOINT_PERSISTENCE_RESULT.md)
then brought six windows inside the reference. A [check of the saved fits](prediction-observed-development/ESA_JOINT_PERSISTENCE_STOPPING_RESULT.md)
found some room for the optimizer to improve in every case. The next check
used those derivatives to [finish all eight fits](prediction-observed-development/ESA_JOINT_PERSISTENCE_ANALYTIC_RESULT.md).
The same two misses remained. An [epoch-by-epoch check](prediction-observed-development/ESA_PERSISTENCE_WINDOW_DIAGNOSTIC_RESULT.md)
found extra north and vertical error throughout one steady window, with
overestimated uncertainty during and after a turn. Other windows in both
categories passed. [Carrying earlier motion across the forecast cut](prediction-observed-development/ESA_PERSISTENCE_HISTORY_RESULT.md)
changed neither outcome. [Allowing more variation between whole windows](prediction-observed-development/ESA_WINDOW_SCALE_MIXTURE_RESULT.md)
brought the turn inside the reference. The high-error steady window remains
outside with the original GPS solution. [Two alternate GPS solutions](prediction-observed-development/ESA_FORECAST_RECEIVER_TRANSFER_RESULT.md)
bring that window inside while several others fall below the reference.
A [receiver-specific error model](prediction-observed-development/ESA_RECEIVER_CONTRAST_COVARIANCE_RESULT.md)
predicts those GPS differences, but the term [does not fit inside the
existing forecast covariance](prediction-observed-development/ESA_RECEIVER_COVARIANCE_COMPATIBILITY_RESULT.md).
A [combined model](prediction-observed-development/ESA_ADDITIVE_RECEIVER_COVARIANCE_RESULT.md)
improves average predictive scores, while the reference fails on six
of eight windows with the original GPS solution. Independent coverage
and common GPS errors remain open.
[A raw carrier check](prediction-observed-development/ESA_RAW_PHASE_PPP_TIMESCALE_RESULT.md)
shows that the difference between position solutions cannot be read
directly from the receivers' carrier differences.
[Across the development flight](prediction-observed-development/ESA_PPP_COVARIANCE_CHRONOLOGY_RESULT.md),
the faster changes carry over from early to late measurements. The
offsets between GPS solutions grow beyond the early error model.
[Recent offsets improve the short forecast](prediction-observed-development/ESA_PPP_OFFSET_FORECAST_RESULT.md).
The model still underestimates how much those offsets can change.

A fixed receiver less than 1 km from the aircraft's Reykjavík ground
stop matched 61 raw GPS times and tracked ten of the same satellites
throughout the stop. The resulting phase path disagrees with the aircraft
GPS path by 0.85 m vertically RMS. The two recorded bands agree to
about a centimetre. Applying the recorded clock corrections still leaves
the vertical disagreement. The integrated Doppler path differed from both
position paths by about 15 m vertically RMS over that half hour, too much
to resolve the difference.
On 90 seconds of matched permanent Nuuk and aircraft data, the range
difference grew from 3.55 cm to 18.90 cm when the test displacement was
added. A second constructed error returns to zero at all four ground times
and still spans the saved score gap. It raises the half-second aircraft
range residual from 3.77 to 4.74 mm RMS. The 1 Hz Nuuk Museum file would
check more of those gaps.
The [final orbit and clock check](prediction-observed-development/ESA_NUUK_ORBIT_CLOCK_RESULT.md)
found that their combined update accounted for essentially none of the range
pattern the test displacement would need.
The [range and position accuracy check](prediction-observed-development/ESA_CARRIER_ANCHOR_ERROR_RESULT.md)
shows which errors could change the score. With a 1 mm RMS carrier-error cap,
it allows about 1 m of error per coordinate at the six reference times under
the stated motion assumptions. The archive has yet to establish those caps.
The [sampling check](prediction-observed-development/ESA_CARRIER_SCORE_CADENCE_RESULT.md)
shows that the actual 30-second ground totals miss the score-sensitive changes
between their samples. Ideal one-second coverage would expose nearly all of
that part of the score, subject to signal coverage and measurement error.
On the aircraft side, the one-second carrier signal for the two-minute test
survives at 9.77 mm RMS.
For ideal one-second coverage, the [score accuracy target](prediction-observed-development/ESA_GROUND_GRID_SCORE_RESULT.md)
is about 4.65 cm on each aircraft position coordinate when error between
samples is negligible. The ground data still need to establish whether
that accuracy is achievable. The [RINEX coverage reader](prediction-observed-development/ESA_NKAR_INTAKE_READY.md)
is ready to verify matching timestamps once the Nuuk Museum file is available.
The [matched score calculation](prediction-observed-development/ESA_NKAR_GROUND_SCORE_PLAN.md)
passed its software checks and will measure how much of the signed comparison
the actual ground observations cover.
The [Qaqortoq one-second comparison](prediction-observed-development/ESA_QAQ_GROUND_SCORE_RESULT.md)
covers 98% of the carrier weight norm. The measured aircraft-minus-ground
discrepancy on those directions is 2.46% of the score gap. The nearer Nuuk file
is still needed to test how much local errors matter.
The [earlier-only Qaqortoq correction](prediction-observed-development/ESA_QAQ_PHASE_TRANSFER_RESULT.md)
changed the later residual RMS by just 0.38%.
The [joint error budget](prediction-observed-development/ESA_REFERENCE_ERROR_BUDGET.md)
shows how the matched range error, the directions missed by the ground receiver
and uncertainty at the reference times can each affect the score. The
[geometry check](prediction-observed-development/ESA_CARRIER_RANGE_REMAINDER_RESULT.md)
bounds the linear approximation once position and motion limits are available.
Independent error caps are still needed.
At 30-second spacing, an [earlier ground correction](prediction-observed-development/ESA_NUUK_PHASE_TRANSFER_RESULT.md)
lowered the later range residual from 4.38 cm to 1.92 cm on the saved aircraft
path. This measures range agreement. Applying the benchmark still requires
an independent aircraft position error estimate. On the saved path, the
[position projection](prediction-observed-development/ESA_NUUK_PHASE_POSITION_RESULT.md)
reduces the peak implied height adjustment from 21.62 to 5.19 cm.
[Ground reference findings and verification](prediction-observed-development/ESA_GROUND_REFERENCE_EVIDENCE.md)
[Permanent Nuuk comparison](prediction-observed-development/ESA_NUUK_GROUND_PHASE_RESULT.md) ·
[What the sample gaps allow](prediction-observed-development/ESA_NUUK_BETWEEN_SAMPLES_RESULT.md) ·
[Aircraft carrier replay](prediction-observed-development/ESA_NUUK_BETWEEN_CARRIER_RESULT.md) ·
[One-second test](prediction-observed-development/ESA_NKAR_CADENCE_RESULT.md)
[Reykjavík clock replay](prediction-observed-development/ESA_FIXED_REFERENCE_CLOCK_RESULT.md) ·
[Doppler check](prediction-observed-development/ESA_FIXED_REFERENCE_DOPPLER_RESULT.md)

Nine of twelve unadjusted ESA forecasts met the fixed accuracy limits.
An adjustment learned from earlier GPS positions brought all three
available rolling misses inside the limits. At one cut, only 25 of the
first 120 later GPS heights fell inside the nominal 95% range.
[Raw accuracy](prediction-observed-development/ESA_RAW_ACCURACY_RESULT.md) ·
[Adjusted comparison](prediction-observed-development/ESA_MATCHED_CONDITIONING_RESULT.md) ·
[Uncertainty](prediction-observed-development/ESA_MATCHED_UNCERTAINTY_RESULT.md)

On a separate window from the same flight, four of 16 primary forecasts met
all four accuracy limits over 400 later positions. All four used the specified
field and the persistent receiver error policy. Longer forecasts make this
choice matter. [Saved forecast check](mixed-tangent-hybrid/ESA_DISPATCH_ACCURACY_RESULT.md)

The [height-role check](prediction-observed-development/ESA_HEIGHT_ROLE_RESULT.md)
found that the adjustment itself reduced the height errors. On a separate
cut, the specified-field globe still scored lowest using only north and
east. We still need to test the stated error ranges on independent flights.

The [long-path scoring check](prediction-observed-development/ESA_STRUCTURED_AXIS_SCORE_RESULT.md)
reproduced the same scores with a fraction of the operator storage. It
allows longer paths to be checked under the same assumptions.

Reconstructing ESA positions from [GPS](prediction-observed-development/ESA_RINEX_CODE_COMPARISON_RESULT.md)
and [GLONASS](prediction-observed-development/ESA_GLONASS_COMPARISON_RESULT.md)
preserved the order of the forecasts on the development flight. The same
antenna supplied both. An absolute receiver accuracy check is still open. The
[path sensitivity check](prediction-observed-development/ESA_SHARED_RECEIVER_ERROR_RESULT.md)
shows why this matters for the accuracy screen even though the ranking
of the fixed forecasts has a much larger margin.
Using [final GPS satellite orbits](prediction-observed-development/ESA_FINAL_ORBIT_REPLAY_RESULT.md)
shifted the later positions by 0.90 m RMS and preserved the forecast
ranking. Changing the [satellite clock corrections over time](prediction-observed-development/ESA_RELATIVE_CLOCK_REPLAY_RESULT.md)
shifted the positions by 0.42 m RMS with the same rank. A matching ground
receiver could check other shared errors.
With the same field in both models, the [shape preference held across eight receiver paths](prediction-observed-development/ESA_SHAPE_RECEIVER_REPLAY_RESULT.md)
even after allowing smooth motion corrections. Some paths came much
closer to a tie. Prediction uncertainty still needs its own test.
The [receiver-margin check](prediction-observed-development/ESA_SHAPE_RECEIVER_MARGIN_RESULT.md)
shows how small a position error can change the result if it follows
the timing of the remaining shape signal.
The [processed receiver exports](prediction-observed-development/ESA_PPP_SHAPE_ERROR_RESULT.md)
agree closely in that score. [Raw GPS carrier phase](prediction-observed-development/ESA_CARRIER_PHASE_LATER_RESULT.md)
also confirms the two-minute relative motion. Extending that test to the
[whole window](prediction-observed-development/ESA_CARRIER_PHASE_CONTINUOUS_RESULT.md)
barely moves the shape score. A [separate GLONASS path](prediction-observed-development/ESA_GLONASS_PHASE_PATH_RESULT.md)
agrees closely in horizontal position and in the score. The larger
height disagreement leaves more uncertainty on that axis.
Two [weather-balloon soundings](prediction-observed-development/ESA_SOUNDING_DELAY_RESULT.md)
give a separate check on one shared assumption. In the [carrier-path replay](prediction-observed-development/ESA_SOUNDING_CARRIER_RESULT.md),
changing the weather shifts the fixed shape score by at most 0.022 units.
Aircraft-local errors and independent-flight accuracy still need testing.
One [solver check](prediction-group-transfer/CURVED_BOUNDED_SOLVER_RESULT.md)
also finds that a solver can get the cost right and still fail the final
position check. The centered objective method passed on known answers,
then ran out of time in the [generated flight test](prediction-group-transfer/CENTERED_FLIGHT_SOLVER_RESULT.md).
The [parameter scaling check](prediction-group-transfer/SCALED_SOLVER_REPLAY_RESULT.md)
helped the math but still missed every required result. The existing
solver remains in use, and the two unmatched ESA settings stay unresolved.
The [ESA direction comparison](prediction-observed-development/ESA_DIRECTION_EXACT_CORRECTION_RESULT.md)
uses the gyro to track changes in the accelerometer's force direction.
After fitting both sensors on the earlier data, the globe predicts the
later directions more closely in 17 of 18 settings. The small disc
preference follows the GLONASS training velocity. [Velocity source swap](prediction-observed-development/ESA_DIRECTION_VELOCITY_TRANSFER_RESULT.md)

The globe also has lower later error when the fit shares one calibration
across receiver sources. The ranking held on eight other windows of the
same flight, where transferring that calibration made the retained-field
globe's angular predictions worse. Future tests need to measure angular
errors and repeat the comparison on independent flights.
[Shared calibration](prediction-observed-development/ESA_DIRECTION_POOLED_CALIBRATION_RESULT.md) ·
[Eight-window transfer](prediction-observed-development/ESA_DIRECTION_WINDOW_TRANSFER_RESULT.md)
Comparing the angles between directions keeps the same shape ranking in
all 48 settings without fitting a starting orientation. It also holds
after accounting for the distance between the sensor and the antenna.
[Angle-pair check](prediction-observed-development/ESA_DIRECTION_ANGLE_PAIRS_RESULT.md) ·
[Antenna offset](prediction-observed-development/ESA_DIRECTION_LEVER_ARM_RESULT.md)

The two force instruments on the ESA development flight disagree more
than the globe and disc predict after removing an earlier offset.
Swapping receiver products also changes the predicted force by more
than the shape difference. Force magnitude alone leaves shape unresolved.
[Two-instrument force check](prediction-observed-development/ESA_GIRAFE_FORCE_CONTRAST_RESULT.md)
A force error that persists across a window predicts later disagreements
better than independent noise. The accuracy still needs verification
on other flights.
[Earlier-to-later check](prediction-observed-development/ESA_GIRAFE_FORCE_ERROR_LAW_RESULT.md)
Both instruments' average force is close to measured gravity at two
airports. Their difference grows by more than a factor of ten in flight.
[Airport reference check](prediction-observed-development/ESA_GIRAFE_GROUND_TIES_RESULT.md)
Matching the instruments' averaging reduces the median airborne
gap from 27.24 to 0.47 mm/s². Training on recordings that used the
same instrument setting gives closer later agreement.
[Matched averaging](prediction-observed-development/ESA_GIRAFE_FORCE_BANDWIDTH_RESULT.md) ·
[Matched error model](prediction-observed-development/ESA_GIRAFE_MATCHED_ERROR_LAW_RESULT.md)

The receiver contributes a separate uncertainty. Its reported velocity
precision leaves the size of persistent errors open, and that matters
when estimating acceleration from velocity.
[Receiver velocity check](prediction-observed-development/ESA_FORCE_VELOCITY_ERROR_RESULT.md)
Removing any one GPS satellite from the carrier calculation preserves the
shape preference on the development window. A separate position reference
is still needed to check errors shared by the satellites.
[Satellite check](prediction-observed-development/ESA_CARRIER_SATELLITE_INFLUENCE_RESULT.md) ·
[Ground reference search](prediction-observed-development/ESA_GROUND_REFERENCE_AVAILABILITY.md)
A 3 cm range error could close the fixed score gap if it lines up in the
most unfavorable way across satellites and time. Independent errors affect
the score much less at the same scale. [Carrier error check](prediction-observed-development/ESA_PHASE_ERROR_SCORE_RESULT.md)
The three raw receiver streams now match on the development window. The two
alternate receivers differ by 1.77 mm RMS in later carrier-range changes.
All three share the aircraft antenna. [Matched raw observations](prediction-observed-development/ESA_PARALLEL_RAW_RECEIVER_RESULT.md)
Applying those differences to the saved route preserves the shape result
with either receiver correction. [Effect on the fixed score](prediction-observed-development/ESA_RAW_RECEIVER_SCORE_RESULT.md)
Rebuilding both paths from Galileo carriers also preserves the preference.
The two Galileo paths agree to about 2 cm RMS over the later window.
[Separate constellation check](prediction-observed-development/ESA_GALILEO_PHASE_PATH_RESULT.md)
The preferred forecast also meets the position limits on all twelve
tested receiver paths across both complete settings.
[Withheld accuracy replay](prediction-observed-development/ESA_RECEIVER_ACCURACY_REPLAY_RESULT.md)
Fitting a shared atmospheric delay to earlier GPS data shifts the later
path by 29 cm. The same forecast still meets the position limits.
[Atmospheric delay check](prediction-observed-development/ESA_CARRIER_DELAY_FIT_RESULT.md)
Calculating acceleration from positions makes the receiver products
agree more closely, but predicts the separate GIRAFE force less well.
[Position derivative check](prediction-observed-development/ESA_FORCE_POSITION_DERIVATIVE_RESULT.md)
The shape ranking from measured directions survives both derivative
methods. Matching how those methods respond to motion resolves most
of the largest disagreement. An absolute accuracy rule still needs
independent evidence.
[Matched derivative check](prediction-observed-development/ESA_MATCHED_RECEIVER_RESPONSE_RESULT.md)
On eight new windows from the same recording, seven had smaller globe
errors under every setting. On the strongest turn, the model with the
smaller error changed with the background-field assumption. Independent
tests need an accuracy rule that handles this difference.
[Prediction check](prediction-observed-development/ESA_DIRECTION_HOLDOUT_SCORE_RESULT.md)
Allowing the full range of the tested gyro processing assumptions leaves
the globe with smaller best-case angle errors in every comparison.
[Field-range check](prediction-observed-development/ESA_DIRECTION_HOLDOUT_FIELD_RANGE_RESULT.md)
Both alternate receiver exports preserve the shape ordering on the first
leg. Matching the second leg needs a common clock phase.
[Receiver check](prediction-observed-development/ESA_DIRECTION_HOLDOUT_RECEIVER_RESULT.md)
All three exports also preserve the ordering on the second leg once the
query times match. The next accuracy check needs a separate sensor.
[Second-leg comparison](prediction-observed-development/ESA_DIRECTION_HOLDOUT_CLOCK_SCORE_RESULT.md)
The separate GIRAFE recorder has a readable clock pattern. Its recorded
times and channels still need to be matched to the flight data.
[Platform check](prediction-observed-development/ESA_GIRAFE_PLATFORM_PROBE_RESULT.md)
The first force-magnitude match was ambiguous. The horizontal channels
also leave the suggested offset unresolved. Three new vertical-force
excerpts agree on the best time, and two fall below the minimum correlation.
[Timing result](prediction-observed-development/ESA_GIRAFE_PLATFORM_VERTICAL_HOLDOUT_RESULT.md)
At longer averaging times the force records agree much more closely.
[Force response](prediction-observed-development/ESA_GIRAFE_PLATFORM_VERTICAL_RESPONSE_RESULT.md)
Two of three excerpts also match the separate iMAR accelerometer. The
middle excerpt still leaves the clock unqualified.
[Separate accelerometer check](prediction-observed-development/ESA_GIRAFE_PLATFORM_IMAR_FORCE_RESULT.md)
The ground check found a strong force match after shifting the proposed time
0.1 seconds earlier. The current rate interpretation made direction error
worse, so using it as a separate turning reference still needs qualification.
[Ground platform check](prediction-observed-development/ESA_GIRAFE_GROUND_RATE_RESULT.md)
The finer replay confirms that ground shift. Airborne timings vary, and
the middle clip stays unmatched. [Ground-to-flight timing](prediction-observed-development/ESA_GIRAFE_FINE_LAG_RESULT.md)
Both [Doppler velocity paths](prediction-observed-development/ESA_DOPPLER_COMPARISON_RESULT.md)
also recovered the two-minute displacement to within a few tenths of a metre.
The [gyro direction calibration check](prediction-observed-development/ESA_GYRO_DIRECTION_CALIBRATION_RESULT.md)
found one allowed accelerometer correction that reverses its ranking.
The [position replay](prediction-observed-development/ESA_X_BIAS_POSITION_REPLAY_RESULT.md)
found that the six tested adjustments failed to recover the earlier
score. A bound across other nonlinear adjustments is still open.
The [continuous X-bias check](prediction-observed-development/ESA_X_BIAS_DIRECTION_PROFILE_RESULT.md)
identifies the positive bias range this next test needs to cover.
The [earlier position bound](prediction-observed-development/ESA_X_BIAS_RANGE_POSITION_RESULT.md)
sets the scale for testing the nonlinear remainder on that range.
The [exact boundary search](prediction-observed-development/ESA_X_BIAS_NONLINEAR_RANGE_RESULT.md)
still exceeds the earlier loss allowance after two corrections.

The calibration bound remains 53.04 units after adding constraints from the
physical calibration. The globe–disc forecast gap is 25.41 units. The bounds
over whole calibration ranges are still too wide to tell whether calibration
could erase that gap.
[Latest calibration check](prediction-observed-development/ESA_LINKED_FULL_LOSS_RESULT.md)
Two relaxed proposals could exceed that gap. They fit the earlier data
poorly when their terms are tied to one physical calibration. The remaining
question is how much a single calibration can change the forecast while
keeping the earlier fit. [Proposal check](prediction-observed-development/ESA_LINKED_FLOOR_WITNESS_RESULT.md)
Testing those loss directions across the full ranges also leaves the
forecast gap unresolved. [Linked range check](prediction-observed-development/ESA_LINKED_FLOOR_SUPPORT_RESULT.md)

**Check what the inertial measurements add.** Across twenty NASA
recording groups, all 18 available head-to-head forecasts had smaller
horizontal errors with the inertial measurements. The GPS-only rule
used the previous minute's course and speed. Height errors were more
mixed. [GPS-only comparison](prediction-group-transfer/REMAINING_GPS_BASELINE_RESULT.md)

**Check accuracy even when a fit fails to stop.** All 104 saved NASA
forecasts met the fixed position-error limits, including 67 with failed
numerical stopping checks. Those failures still count. The study uses
earlier recordings from the same archive. [Accuracy audit](prediction-group-transfer/ACCURACY_MARGIN_RESULT.md)

**Check what acceleration can explain by itself.** On two recordings,
the force-only test leaves all four models possible. One GPS correction
of at most 27 cm cleared the remaining gaps on one recording. The other
needed no correction. The same correction left all saved IMU forecast
rankings unchanged. [Shared GPS error check](ilvis0-measurement-contribution/SHARED_FORCE_WITNESS_RESULT.md) ·
[Forecast comparison](ilvis0-measurement-contribution/SHARED_FORCE_FORECAST_RESULT.md)

**Check the aircraft motion implied by acceleration alone.** The same
GPS correction barely changed the rate bounds on the IMU8 recording.
All four cases still overlap under both clocks in both parts of the
recording. A catalog search found no timed camera images during either
comparison stretch. [Gyro-free rate comparison](ilvis0-measurement-contribution/SHARED_GPS_MOTION_RATE_RESULT.md) ·
[Aircraft-motion sources](ilvis0-measurement-contribution/MOTION_SOURCE_AUDIT.md)

**Check when the turn allowance helps.** All four turns scored
better with an allowance for turn-related uncertainty. When the same turn
timing was assigned to steady flight, all four scores got worse. A single
multiplier could not account for the errors. Smooth height drift explained
most of the largest steady-flight error. The turn errors still varied
widely after accounting for smooth drift.
[Steady-flight comparison](prediction-observed-development/ESA_STRAIGHT_CONTROL_RESULT.md) ·
[Drift check](prediction-observed-development/ESA_SCORED_PATH_SHAPE_RESULT.md)

**Put a physical limit on drift corrections.** A smooth correction can
absorb most of the globe–disc forecast gap in metres. The working
covariance still assigns weight to smaller differences in path shape.
Use earlier data to bound the corrections and test those weights.
[Matched path check](prediction-observed-development/MATCHED_SHAPE_DRIFT_RESULT.md)

**Establish the size and time pattern of aircraft forecast errors.** On
one opened ESA flight, accounting for correlated receiver errors left
24–62 m between the three predicted paths. Changes to the 27 fitted
calibration parameters could close less than 0.37 m under the test's
earlier-fit allowance. The standardized squared error was four times
as large in the later of two held-out windows on the same flight.
Most of the increase in the east-ordered score followed a turn, and a
term that allows brief acceleration errors helped explain it separately
from the height drift in straight flight. Two preselected windows contain
maneuvers that could help test the brief error separately. A generated
check recovered both scales while fitting a simple flight path. On the
saved ESA interval, flight calibration can absorb nearly all the steady
error pattern. The two ground stops barely improve that result even if
their force magnitudes are treated as exact. The gyro also tracks much of
the tilt at the first stop, showing why low speed alone cannot establish a
stationary noise reference. [Ground tilt check](prediction-observed-development/ESA_GROUND_TILT_CLOSURE_RESULT.md)
Receiver velocity shows
stronger airborne maneuvers. Receiver positions give a more precise
acceleration estimate. Averaging the accelerometer's force vectors for
0.1 seconds before taking their magnitudes removes most of the large
disagreement in one window. Using that variation to estimate position
uncertainty made scores worse. Separate checks now find that the height
drift in straight flight and the east error after a turn respond to
different corrections. Four new receiver-selected windows on the same
flight contain isolated turns and have passed the input timing check.
The scoring software passed generated checks using a fixed maneuver
scale. All 16 starts passed, and the eight selected forecasts had later
three-dimensional position errors of 0.44–1.97 m RMS. The turn allowance
improved the score in all four windows. Adding both allowances worked
best in three. We also need a rule for how close a prediction must be before we test
the method on independent flights.
[Calibration comparison](prediction-observed-development/ESA_CONDITIONED_CALIBRATION_RESULT.md) ·
[Error and aircraft motion](prediction-observed-development/ESA_MOTION_ERROR_LAW_RESULT.md) ·
[Preselected motion windows](prediction-observed-development/ESA_COMPONENT_PREFLIGHT_RESULT.md) ·
[Aircraft calibration check](prediction-observed-development/ESA_GROUND_FORCE_SUPPORT_RESULT.md) ·
[Fast force and prediction errors](prediction-observed-development/ESA_FAST_FORCE_TRANSFER_RESULT.md) ·
[Straight-flight and turn corrections](prediction-observed-development/ESA_ERROR_SHAPE_TRANSFER_RESULT.md) ·
[Repeat-turn forecast results](prediction-observed-development/ESA_REPEAT_TURN_FORECAST_RESULT.md) ·
[Steady-course comparison](prediction-observed-development/ESA_STRAIGHT_CONTROL_PLAN.md) ·
[Forecast scoring checks](prediction-observed-development/ESA_REPEAT_TURN_SCORING_RESULT.md) ·
[Requirements for testing independent flights](ESA_ERROR_POLICY.md#from-development-comparisons-to-an-independent-flight-test) ·
[How the decision counts flights](FLIGHT_GROUP_DECISION.md)

**Keep NASA checks grouped by flight evidence.** The four matched groups
already appear in earlier studies. The new table puts each group's fitted
comparisons, held-back predictions and paired-sensor checks on one row.
One group still lacks a zero-field disc forecast. The next confirmation
needs separate flight groups and a qualified error model.
[All 27 recording groups](analysis-provenance/NASA_GROUP_EVIDENCE.md)

**Count the ESA evidence by recording.** The principal forecast results all
come from one development group. Some shorter forecasts test positions used
to train a longer fit. The [ESA cut table](analysis-provenance/ESA_GROUP_EVIDENCE.md)
shows that reuse and keeps the seven reserved groups separate. Each reserved
group has one [20-minute slice with continuous IMU timestamps](external-imu-data/ESA_CONFIRMATION_TIMING_RESULT.md).

## Five questions still open

| Question | What needs to happen |
|---|---|
| **Can the models predict positions they have not seen?** | Validate an absolute prediction-error rule that accounts for how aircraft errors change over time. |
| **What does the gyroscope add?** | Compare matched fits with and without the gyro measurements. The current acceleration-only check leaves the aircraft's orientation too uncertain to rule out a candidate. |
| **Does the result repeat on independent flights?** | Qualify the aircraft error model and freeze the forecast rules before fitting the seven reserved ESA flight groups. |
| **How certain is the result across flights?** | The score and decision software passes known-answer checks. Calibrate it using aircraft-relevant errors and validate it across flight groups. |
| **What angular field do the measurements imply?** | Estimate the field's strength and direction freely. Distinguishing solar and sidereal rates would require much tighter precision and bias control. |

[Technical milestones](ANALYSIS_ROADMAP.md#current-milestones-and-finish-line) ·
[Flight-group decision rule](FLIGHT_GROUP_DECISION.md) ·
[Free-field study](ROTATION_FIELD.md)

## Study records

The [study guide](STUDY_GUIDE.md) gives a short route through the completed
work. The [full study record](STUDIES.md) and
[reproducibility guide](REPRODUCIBILITY.md) retain the methods, failures
and evidence. The [53-stretch table](ilvis0-current-findings-20261015/STRETCHES.md)
and [detailed CSV](ilvis0-current-findings-20261015/stretch-analytics.csv)
show what was measured and how each stretch was classified.
