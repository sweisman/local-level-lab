# Archived studies

This page preserves the earlier research record. Statements about what comes next reflect those study stages. See the [current page](STUDIES.md) for the active status and plan.

# Studies and what each added

Two [GPS code reconstructions](prediction-observed-development/ESA_RINEX_CODE_RESULT.md)
solved all 1,041 epochs. Both [preserved the order of the existing ESA forecasts](prediction-observed-development/ESA_RINEX_CODE_COMPARISON_RESULT.md)
over the same 120 later positions.

The [final satellite-product check](prediction-observed-development/ESA_PRECISE_GPS_SUPPORT_RESULT.md)
verified orbit coverage for all 12,354 GPS observations used in that
solution. One satellite lacks the 30-second clock series.
The [final orbit replay](prediction-observed-development/ESA_FINAL_ORBIT_REPLAY_RESULT.md)
shifted the later positions by 0.90 m RMS and preserved both matched
forecast rankings.
The [matched clock replay](prediction-observed-development/ESA_RELATIVE_CLOCK_REPLAY_RESULT.md)
kept the same satellite set while changing the time-varying clock
corrections. It shifted the later positions by 0.42 m RMS and preserved
both forecast rankings.
The [matched-field receiver replay](prediction-observed-development/ESA_SHAPE_RECEIVER_REPLAY_RESULT.md)
compares globe and disc with zero background field and allows smooth
motion corrections. All eight paths favor globe, with the GPS L1 path
closest to a tie.
The [receiver-margin check](prediction-observed-development/ESA_SHAPE_RECEIVER_MARGIN_RESULT.md)
finds the size and timing of a position error that would reverse that
fixed score. It supplies thresholds for testing the receiver error model.
The [processed receiver check](prediction-observed-development/ESA_PPP_SHAPE_ERROR_RESULT.md)
measures much smaller differences in that score across the three exports.
The full-flight probe retains all 195 fast windows per export, including
seven excluded for overlap.
The [carrier-phase replay](prediction-observed-development/ESA_CARRIER_PHASE_LATER_RESULT.md)
recovers two minutes of GPS motion from raw phase changes and one earlier
position. It agrees with the original export within 12.3 cm RMS and
preserves the fixed shape preference.
The [continuous carrier replay](prediction-observed-development/ESA_CARRIER_PHASE_CONTINUOUS_RESULT.md)
checks the earlier clock step and uses one anchor for all 520 reports.
It recovers the earlier and later trajectory with nearly the same
shape score as the later-only replay.
The [single-satellite check](prediction-observed-development/ESA_CARRIER_SATELLITE_INFLUENCE_RESULT.md)
estimated the effect of omitting each of 12 satellites and preserved the
fixed shape preference in every case.
The [carrier phase-error check](prediction-observed-development/ESA_PHASE_ERROR_SCORE_RESULT.md)
traced all 1,038 phase differences to their original observations and
measured the fixed score's sensitivity to several error patterns.
The [parallel raw receiver preflight](prediction-observed-development/ESA_PARALLEL_RAW_RECEIVER_PREFLIGHT.md)
verified the headers and sampling of two additional same-flight archive files.
The [matched receiver study](prediction-observed-development/ESA_PARALLEL_RAW_RECEIVER_RESULT.md)
verified the full interval and compared identical GPS carrier signals across
the three receivers at 518 one-second steps.
The [relative receiver-score check](prediction-observed-development/ESA_RAW_RECEIVER_SCORE_RESULT.md)
applied both sets of differences to the fixed shape comparison. The original
preference survived both path corrections.
The [Galileo-only replay](prediction-observed-development/ESA_GALILEO_PHASE_PATH_RESULT.md)
reconstructed 519 steps on each receiver using final ESOC orbits and clocks.
Both paths preserved the fixed shape preference.
The [withheld accuracy replay](prediction-observed-development/ESA_RECEIVER_ACCURACY_REPLAY_RESULT.md)
scored the six fixed forecasts on twelve paths. The preferred model met
the original position limits in all 24 comparisons.
The [earlier-only atmospheric delay fit](prediction-observed-development/ESA_CARRIER_DELAY_FIT_RESULT.md)
shifted one later carrier path by 0.29 m RMS and preserved the fixed shape and
position-check results.
The [GLONASS carrier replay](prediction-observed-development/ESA_GLONASS_PHASE_PATH_RESULT.md)
repeats the continuous path with a separate satellite constellation.
Both paths preserve the shape preference despite a larger height difference.
The [weather-balloon comparison](prediction-observed-development/ESA_SOUNDING_DELAY_RESULT.md)
finds centimetre-scale differences from the standard atmosphere in the
estimated overhead signal delay. The balloons were hundreds of kilometres
from the aircraft.
The [matched regional-weather replay](prediction-observed-development/ESA_SOUNDING_CARRIER_RESULT.md)
then finds that all four recorded paths preserve the fixed shape ranking.
The saved-path audit retains the original runner's result-record failures.

The [curved solver control](prediction-group-transfer/CURVED_BOUNDED_SOLVER_RESULT.md)
checks three numerical methods against exact optima. The current trust region
and a centered objective method pass every case. SciPy TRF fails six final
position checks despite small objective gaps.
In the [short generated flight test](prediction-group-transfer/CENTERED_FLIGHT_SOLVER_RESULT.md),
the current solver passed its first fit in 10 evaluations. The centered
solver reached the time limit after 182 attempts on the same input.
The [saved-derivative scaling test](prediction-group-transfer/SCALED_SOLVER_REPLAY_RESULT.md)
then finds that both centered versions fail all seven known-target controls
with the full set of calibration columns.

The [ESA force-direction forecast](prediction-observed-development/ESA_FORCE_DIRECTION_TRANSFER_RESULT.md)
fits one frame rotation on eight directions and scores eight later ones.
It favors the globe at nominal calibration. One accelerometer correction
reverses the retained-field comparison, leaving calibration open.
In the [earlier-only X-bias test](prediction-observed-development/ESA_DIRECTION_BIAS_TRAINING_RESULT.md),
both candidates can estimate that correction from eight directions.
The globe has lower later angular error in all 18 comparisons. The
one-axis restriction and unmeasured angular error still limit the result.
The [all-axis accelerometer check](prediction-observed-development/ESA_DIRECTION_ACCEL_CALIBRATION_RESULT.md)
then preserves that ranking with three biases and three gains. It retains
the gyro increments as logged and makes no calibrated accuracy claim.
The [joint gyro and accelerometer replay](prediction-observed-development/ESA_DIRECTION_JOINT_CALIBRATION_RESULT.md)
finds a much smaller separation after fitting all 12 calibration
coordinates. One retained-field sensitivity setting favors the disc.
The [exact-gradient audit](prediction-observed-development/ESA_DIRECTION_EXACT_GRADIENT_RESULT.md)
reproduces the earlier losses and finds that all 108 saved points fail the
original stopping threshold when evaluated with exact packet derivatives.
The [exact correction](prediction-observed-development/ESA_DIRECTION_EXACT_CORRECTION_RESULT.md)
passes the stopping check for all 36 new fits. It retains one disc
preference among the 18 sensitivity settings.
The [velocity source swap](prediction-observed-development/ESA_DIRECTION_VELOCITY_TRANSFER_RESULT.md)
holds each calibration fixed and uses three sources to score it. The
reversal tracks which velocity trained the fit.
The [shared calibration check](prediction-observed-development/ESA_DIRECTION_POOLED_CALIBRATION_RESULT.md)
uses all three velocity products and each two-source subset in the
previously reversed setting. All 18 fits pass the exact stop, and the
globe has lower later angle error in all 27 paired scores.
The [eight-window transfer](prediction-observed-development/ESA_DIRECTION_WINDOW_TRANSFER_RESULT.md)
keeps the ranking under nominal and transferred calibration. The transferred
calibration increases retained-field globe errors in all 16 such settings.
The [angle-pair check](prediction-observed-development/ESA_DIRECTION_ANGLE_PAIRS_RESULT.md)
finds a lower globe error in all 48 nominal-calibration comparisons
without fitting a starting orientation, including all 16 zero-field
comparisons.
The [antenna offset check](prediction-observed-development/ESA_DIRECTION_LEVER_ARM_RESULT.md)
keeps all 48 comparisons in the same order after applying the campaign's
published sensor-to-antenna offset.
The [GIRAFE force comparison](prediction-observed-development/ESA_GIRAFE_FORCE_OVERLAP_RESULT.md)
matches the same eight windows to a second instrument. It finds a
persistent 26–29 mm/s² mean difference and closely matching changes.
The [force-only model check](prediction-observed-development/ESA_GIRAFE_FORCE_CONTRAST_RESULT.md)
finds that the predicted shape difference is smaller than both the
observed sensor discrepancy and the receiver sensitivity in every
matched setting, after accounting for the earlier offset.
The [chronological error check](prediction-observed-development/ESA_GIRAFE_FORCE_ERROR_LAW_RESULT.md)
fits the force difference on the first four windows and predicts the
last four. Including a shared error across each window improves
the later score at both widths.
The [airport gravity check](prediction-observed-development/ESA_GIRAFE_GROUND_TIES_RESULT.md)
links the two ground stops to measured apron gravity. The two force
instruments agree much more closely on the ground than they do in flight.
The [matched-averaging replay](prediction-observed-development/ESA_GIRAFE_FORCE_BANDWIDTH_RESULT.md)
reduces the median airborne difference from 27.24 to 0.47 mm/s²
by averaging the vectors in the same time cells before taking their
magnitudes. The [matched error-law replay](prediction-observed-development/ESA_GIRAFE_MATCHED_ERROR_LAW_RESULT.md)
finds closer agreement on the four later windows when training uses
the same constant instrument setting.
The [velocity uncertainty replay](prediction-observed-development/ESA_FORCE_VELOCITY_ERROR_RESULT.md)
tests how errors that persist across receiver reports affect the
force predictions. The uncertainty in each prediction is much larger
than the uncertainty in their difference when both use the same input.
The [position derivative check](prediction-observed-development/ESA_FORCE_POSITION_DERIVATIVE_RESULT.md)
uses the same time supports. Position-derived predictions agree more
closely across receiver products and less closely with measured force.
The [receiver-derivative direction replay](prediction-observed-development/ESA_DIRECTION_RECEIVER_DERIVATIVE_RESULT.md)
keeps all 576 globe–disc rankings. One position-derived window still
has large angle errors under both models. The
[matched differentiation check](prediction-observed-development/ESA_MATCHED_RECEIVER_RESPONSE_RESULT.md)
reduces the largest difference between prediction methods to 0.030°
and preserves every ranking.
The [receiver-only window selection](prediction-observed-development/ESA_DIRECTION_HOLDOUT_SELECTION_RESULT.md)
saves eight disjoint windows across two flight legs before their gyro data
are scored. The [sealed predictions](prediction-observed-development/ESA_DIRECTION_HOLDOUT_FORECAST_RESULT.md)
record all predicted angles and the earlier error references before any
new inertial data are read.
The [score on the new windows](prediction-observed-development/ESA_DIRECTION_HOLDOUT_SCORE_RESULT.md)
gives the globe smaller errors on seven windows across all settings. The
remaining turn favors disc at zero field and globe with the specified field
retained. Both legs belong to the same development recording.
The [field-range check](prediction-observed-development/ESA_DIRECTION_HOLDOUT_FIELD_RANGE_RESULT.md)
then bounds the best errors across all retained fractions of the specified
field. The globe error bound stays below the disc error bound in all 64
comparisons from these eight windows.
The [alternate receiver check](prediction-observed-development/ESA_DIRECTION_HOLDOUT_RECEIVER_RESULT.md)
repeats all 64 first-leg comparisons with the same globe preference. Both
receiver tasks leave the second leg unresolved because of unmatched times.
The [whole-second selection](prediction-observed-development/ESA_DIRECTION_HOLDOUT_CLOCK_RESULT.md)
gets complete matches across the three exports in the same second-leg
cells and seals the inputs before the shifted angles are scored.
The [second-leg scores](prediction-observed-development/ESA_DIRECTION_HOLDOUT_CLOCK_SCORE_RESULT.md)
preserve all 96 field-range preferences. The turn still favors the disc
at zero field, and the globe when the specified field is retained.
The [GIRAFE byte probe](prediction-observed-development/ESA_GIRAFE_PLATFORM_PROBE_RESULT.md)
checks a possible second motion sensor. Its 381 interior rows share the
prefix's relative clock pattern. Their absolute time and channel mapping
need checking before comparison with the iMAR.
The [force-magnitude timing test](prediction-observed-development/ESA_GIRAFE_PLATFORM_TIMING_RESULT.md)
does not qualify the clock. The first excerpt misses its correlation
requirement, and the two later excerpts suggest a common offset to test.
The [horizontal-channel check](prediction-observed-development/ESA_GIRAFE_PLATFORM_COMPONENT_TIMING_RESULT.md)
completes all nine saved-input comparisons. None confirms the proposed
offset under the tested axis mapping.
The [vertical holdouts](prediction-observed-development/ESA_GIRAFE_PLATFORM_VERTICAL_HOLDOUT_RESULT.md)
all peak at the same candidate clock offset. One of three passes the
fixed correlation rule, so timing qualification remains open.
The [response diagnostic](prediction-observed-development/ESA_GIRAFE_PLATFORM_VERTICAL_RESPONSE_RESULT.md)
finds correlations above 0.93 on those same excerpts with 1.1-second
averaging. The [separate iMAR check](prediction-observed-development/ESA_GIRAFE_PLATFORM_IMAR_FORCE_RESULT.md)
matches two excerpts. The middle excerpt falls short even when shifted, so
the clock remains unqualified.
The [local rate screen](prediction-observed-development/ESA_GIRAFE_PLATFORM_RATE_RESULT.md)
selects radians per second in the original axis order from 96 interpretations.
It improves the two holdouts at tenth-second separation and increases their
one-second errors. The channels remain unqualified for flight comparisons.
The [first-ground-stop check](prediction-observed-development/ESA_GIRAFE_GROUND_RATE_RESULT.md)
finds all three force matches peak 0.1 seconds earlier than the proposed
time. The fixed clock and the rate convention both miss their checks.
The [fine-lag replay](prediction-observed-development/ESA_GIRAFE_FINE_LAG_RESULT.md)
reproduces all previous coarse scores and still selects 100 ms earlier on
the ground. The same shift matches two airborne clips after averaging.
Their peaks disagree, and the middle clip has no strong match.

The [GLONASS check](prediction-observed-development/ESA_GLONASS_COMPARISON_RESULT.md)
recovered the same ranking using a different constellation and the same
aircraft antenna.

The [Doppler motion check](prediction-observed-development/ESA_DOPPLER_COMPARISON_RESULT.md)
reconstructed velocity with each constellation and checked the export's
two-minute displacement to within 0.30 m horizontal RMS.

The [accelerometer-only Doppler check](prediction-observed-development/ESA_DOPPLER_FORCE_RESULT.md)
leaves shape unresolved. The change in required force between the
receiver sources is larger than the matched-field shape contrast.

The [gyro direction check](prediction-observed-development/ESA_GYRO_FORCE_DIRECTION_RESULT.md)
tracks how the force direction changes without assuming an initial
heading. The specified-field globe gives the smallest error in all
six comparisons under the retained-field assumption.

The [matched-field comparison](prediction-observed-development/ESA_MATCHED_GYRO_DIRECTION_RESULT.md)
lets globe and disc share a background field and vary how much remains
in the gyro. The globe still gives the smaller directional error in all
six comparisons.

The [calibration replay](prediction-observed-development/ESA_GYRO_DIRECTION_CALIBRATION_RESULT.md)
finds a reversal at one allowed X-axis accelerometer bias. Whether
that correction agrees with the earlier position observations is open.

The [earlier position replay](prediction-observed-development/ESA_X_BIAS_POSITION_REPLAY_RESULT.md)
found that the tested X-bias endpoint adjustments did not recover the
original fit scores. The result leaves other nonlinear adjustments open.

The [ground bias check](prediction-observed-development/ESA_GROUND_X_BIAS_RESULT.md)
finds that the reversing correction worsens force consistency at both
stops even with a separate unknown gravity at each site.

The [continuous X-bias check](prediction-observed-development/ESA_X_BIAS_DIRECTION_PROFILE_RESULT.md)
finds where the globe preference is guaranteed when only X bias
varies. The ground check does not rule out larger positive values.

The [earlier affine position bound](prediction-observed-development/ESA_X_BIAS_RANGE_POSITION_RESULT.md)
keeps the specified-field globe below the direction threshold within
its saved linear model and leaves other calibration explanations open.

The [exact boundary search](prediction-observed-development/ESA_X_BIAS_NONLINEAR_RANGE_RESULT.md)
improved the earlier path at the positive X threshold. No tested
point recovered the original weighted loss.

The [shared GPS error check](prediction-observed-development/ESA_SHARED_RECEIVER_ERROR_RESULT.md)
found a kilometre-scale margin for the fixed forecast ranking and a
metre-scale margin for the position-accuracy screen.

The [long-path scoring check](prediction-observed-development/ESA_STRUCTURED_AXIS_SCORE_RESULT.md)
reproduced the 80 ESA scores and used 21 MB of operator storage at
4,096 generated later positions. A dense three-axis factor at that
length would need 1.21 GB.

The [ESA height-role check](prediction-observed-development/ESA_HEIGHT_ROLE_RESULT.md)
found that earlier GPS adjustment improved the 800-cut height forecast,
while 95 of 120 heights still lay outside the stated ranges. The separate
400-cut model ranking held when only north and east were scored.

The [gyro-free motion check](ilvis0-measurement-contribution/SHARED_GPS_MOTION_RATE_RESULT.md)
reused 608 IMU8 windows and the same 27 cm GPS correction. All four
cases still overlapped under both clocks in both periods.

The [aircraft-motion source check](ilvis0-measurement-contribution/MOTION_SOURCE_AUDIT.md)
found no overlapping timed LVIS images and identified a one-second NCAR
file that may provide context for the IMU21 recording.

The [NASA group evidence table](PAPER_DATASET.md#prediction-evidence-kept-separately)
links all 27 groups to their saved prediction checks. It keeps the
three-model pilot separate from the single-model transfer forecasts.
The [zero-field cost audit](analysis-provenance/NASA_ZERO_FIELD_BY_GROUP.md)
uses the same groups to show where the two zero-field shape fits agree
across stretches and where their rankings differ within a group.
The [current group ledger](analysis-provenance/NASA_GROUP_EVIDENCE.md) joins
those results to the four-group forecast audit and two paired-sensor checks.
Every added result belongs to a group already in the ledger.

Both solvers agreed on all 16 matched pairs on one ESA development
window. At nearby starting points that fit equally well, their forecasts
differed by less than 0.27 mm. [Solver comparison](mixed-tangent-hybrid/OBSERVED_DISPATCH_FRESH_RESULT.md)
The [short recorded ESA timing study](mixed-tangent-hybrid/ESA_SHORT_FIT_TIMING_RESULT.md)
measured 2.19–2.84× fit CPU speedups for the two globe settings. Both pairs
converged and met the numerical agreement checks.
The [full-window benchmark](mixed-tangent-hybrid/ESA_FULL_FIT_TIMING_RESULT.md)
passed both comparisons on the 800-position training window. The selective
calculation used 41–42% less fit CPU time, with computed positions
agreeing within 0.17 micrometres. Later receiver positions stayed withheld.

The [packet-bound profile](prediction-observed-development/ESA_PACKET_BOUND_PROFILE_RESULT.md)
reproduces both recorded prefixes and measures the time spent on
transport, source bounds and buffer handling. Full-history bounds remain open.
The [width-cache benchmark](prediction-observed-development/ESA_PACKET_WIDTH_CACHE_RESULT.md)
reproduces all four bound files and misses its speed gate. The original
calculation stays in use.
The [recorded prefix growth check](prediction-observed-development/ESA_PACKET_BOUND_GROWTH_RESULT.md)
matches all eight predicted centres. The propagated bounds exceed the
engineering target by 4.55 seconds in both candidates.
The [position-budget trace](prediction-observed-development/ESA_POSITION_BOUND_BUDGET_RESULT.md)
reproduces all eight bounds and shows that the residual-velocity allowance
accounts for nearly all of the accumulated departure at 9.55 seconds.

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

The [coordinate-range check](prediction-observed-development/ESA_LINKED_COORDINATE_RESULT.md)
tightened all eleven surviving calibration boxes. The combined upper bound
fell to 53.10 units. The [joint score check](prediction-observed-development/ESA_LINKED_JOINT_SCORE_RESULT.md)
lowered it to 53.04 units against the 25.41-unit forecast gap. The zero-field
comparison remains unresolved over the full calibration range.
The [direct threshold check](prediction-observed-development/ESA_LINKED_SCORE_FLOOR_RESULT.md)
tested the earlier loss at 44 forecast-score thresholds; the bound stayed unchanged.
The [physical calibration cuts](prediction-observed-development/ESA_LINKED_GRAPH_CUTS_RESULT.md)
excluded only two proposed points and reduced the bound by less than 0.001 units.
The [earlier residual projection](prediction-observed-development/ESA_LINKED_FULL_LOSS_RESULT.md)
could remove less than 0.07% of the squared-loss budget and left the combined
bound effectively unchanged. All eleven checks closed without new trajectory fits.
The [proposal reconstruction](prediction-observed-development/ESA_LINKED_FLOOR_WITNESS_RESULT.md)
found 20 near-feasible relaxed points. Every point exceeded the original
earlier loss allowance when its terms were tied to a physical calibration.
The [linked range check](prediction-observed-development/ESA_LINKED_FLOOR_SUPPORT_RESULT.md)
used the resulting loss directions to test 20 thresholds over the full
boxes. None lowered the combined bound.

On the ESA development flight, [a GPS-only comparison](prediction-observed-development/ESA_ROLLING_GPS_CONTROL_RESULT.md)
found smaller horizontal errors with the inertial measurements at three
of four cuts. GPS velocity held constant gave the smallest error at the
fourth. Inertial forecasts gave smaller height errors at all four cuts.

The [initial accuracy audit](prediction-observed-development/ESA_ABSOLUTE_ACCURACY_RESULT.md) mixed raw and
adjusted forecasts. The [raw-only audit](prediction-observed-development/ESA_RAW_ACCURACY_RESULT.md) scored all
twelve before adjustment. The [early warning check](prediction-observed-development/ESA_TRAINING_WARNING_RESULT.md)
flagged the largest later miss and missed the other two.

[Subdividing the calibration ranges](prediction-observed-development/ESA_LINKED_SPLIT_RESULT.md) excluded
three of 18 ranges. [Checking the remaining ranges individually](prediction-observed-development/ESA_LINKED_CHILD_CERTIFICATES_RESULT.md)
excluded four more. [Rescaling the solver](prediction-observed-development/ESA_LINKED_SCALED_PROPOSALS_RESULT.md)
tightened three individual bounds. The [loss-tangent solver check](prediction-observed-development/ESA_LINKED_LOSS_TANGENTS_RESULT.md)
left the then-current 53.20-unit bound unchanged.

The [ESA calibration follow-up](prediction-observed-development/SHAPE_REMAINDER_METRES_RESULT.md)
sets a four-centimetre position-error target under four working covariances.
Meeting that target would preserve the local globe–disc score separation
if the earlier fit-error bound also holds. The shared-prefix predictor
now includes the altitude correction. A [generated check](prediction-observed-development/SHAPE_GRAVITY_HISTORY_RESULT.md)
kept the largest remainder below 0.315 mm on a coarse 40-second history.
The [shared force calculation](prediction-observed-development/SHARED_FORCE_INTEGRALS.md)
then reproduced 24 reports exactly while cutting 24 packet scans to one.
The [outward-rounded initial-force policy](prediction-observed-development/SHAPE_INITIAL_FORCE_RESULT.md)
passed all four original zero-centred cases.
The [first archived-packet check](prediction-observed-development/ESA_SHAPE_PREFIX_PREFLIGHT_RESULT.md)
matched both disc positions. The globe bound ran out of time, so the
original pair remains unresolved. The [faster calculation](prediction-observed-development/ESA_SOURCE_TRANSFER_CHECK.md)
then completed both checks within the same limits. Its disc reports
matched byte for byte, and the full-flight error bound remains open.
The [shared coefficient check](prediction-observed-development/ESA_SHARED_PROFILE_RESULT.md)
then identified the force transform as the main shared contributor to the
uncertain shape score in the fixed 3 cm covariance case.
The [coupled force map](prediction-observed-development/ESA_FORCE_SCORE_RESULT.md)
brought the total shared reduction below 8.55 standardized units. This
leaves a conditional 1.35 cm target for the other position errors.
The [joint earlier-loss check](prediction-observed-development/ESA_LINKED_TRAINING_SUPPORT_RESULT.md)
reduced the upper bound on combined calibration movement from 687 to
about 103 units. That still exceeds the 25.41-unit forecast difference.
The [joint force-map check](prediction-observed-development/ESA_JOINT_FORCE_SUPPORT_RESULT.md)
tightened that bound by less than one unit in each scenario, locating the
remaining uncertainty in the other terms of the calculation.
The [calibration examples](prediction-observed-development/ESA_CALIBRATION_WITNESS_RESULT.md)
show why the wider bound persists. Independently varying shared terms
can exceed the nominal forecast difference, while the same physical
movements fail the earlier GPS check when their shared terms are linked.
The [whole-box static constraints](prediction-observed-development/ESA_COUPLED_TRAINING_SCORE_RESULT.md)
retained all linked examples but yielded a wider score bound than the
previous force-specific calculation.
The [direct support check](prediction-observed-development/ESA_DIRECT_TRAINING_SCORE_RESULT.md)
verified feasible combined movement around 80 units under those same
constraints, above the 25.41-unit forecast difference.
The [bias and force product check](prediction-observed-development/ESA_ACCELERATION_PRODUCT_SCORE_RESULT.md)
narrowed the upper bound slightly. A disc example still exceeds the
forecast difference while meeting the relaxed constraints.
The [attitude-range check](prediction-observed-development/ESA_ATTITUDE_COVER_SCORE_RESULT.md)
covered the full calibration range and lowered the combined bound
from 78.52 to 60.97 units. The forecast difference remains 25.41 units.
The [refinement](prediction-observed-development/ESA_ATTITUDE_REFINEMENT_SCORE_RESULT.md)
checked 32 smaller ranges. One per parent kept its old bound, so the
combined maximum remained 60.97 units.
The [earlier-loss feasibility check](prediction-observed-development/ESA_ATTITUDE_FEASIBILITY_RESULT.md)
excluded 17 ranges and reduced the combined maximum to 54.01 units.
The [scaled survivor check](prediction-observed-development/ESA_ATTITUDE_SURVIVOR_SCORE_RESULT.md)
verified a disc movement of 31.86 units under the relaxed constraints.
Both high-scoring points failed earlier GPS when their shared terms
were linked to a single calibration.
The [linked search](prediction-observed-development/ESA_LINKED_PHYSICAL_SCORE_RESULT.md)
found attainable movements totaling 12.54 units under the working
earlier error allowance. This establishes examples within the saved
map and leaves the global upper bound open.
The [full integrating-model replay](prediction-observed-development/ESA_LINKED_PHYSICAL_REPLAY_RESULT.md)
confirmed 0.432 units of combined movement at the original earlier
loss limit. The two larger movements failed that limit. Reusing the
saved bounds at zero assumed earlier unshared error still gives a
53.66-unit upper bound, above the 25.41-unit forecast difference.
The [linked directional check](prediction-observed-development/ESA_LINKED_DIRECTIONAL_RESULT.md)
completed 36 bounds across nine ranges. Four tightened relative to the
original cover and the combined bound stayed at 53.66 units.

The [twenty-group GPS-only comparison](prediction-group-transfer/REMAINING_GPS_BASELINE_RESULT.md)
completed all 40 forecasts. All 18 matched IMU forecasts had smaller
horizontal errors. At the later cut, GPS alone had lower height error
in five of nine comparisons.

The [shared GPS error check](ilvis0-measurement-contribution/SHARED_FORCE_WITNESS_RESULT.md)
removed all 16 IMU8 force-only gaps with a shared correction of at most
0.272 m per epoch. IMU21 passed those checks at zero correction. The first
IMU8 attempt stopped at the time cap and remains archived.
The [same correction](ilvis0-measurement-contribution/SHARED_FORCE_FORECAST_RESULT.md)
preserved both paired forecast rankings on the same two recordings at all
four horizons. No model fit or propagation was repeated.

The [fixed accuracy audit](prediction-group-transfer/ACCURACY_MARGIN_RESULT.md)
found all 104 archived forecasts within the transfer study's accuracy
limits. It retained the 67 failed stops and checked the saved margins
after a completion-envelope error.

The [earlier-to-later drift check](prediction-group-transfer/ERROR_TRANSFER_RESULT.md)
reduced height RMS on 15 of 20 groups and horizontal RMS on three.
One corrected horizontal forecast missed the fixed accuracy screen.
The [height-only check](prediction-group-transfer/HEIGHT_TRANSFER_RESULT.md)
improved height RMS in all seven additional groups while preserving the
horizontal scores and original stopping labels.

For the short account, start with [the research in order](STUDY_GUIDE.md).
This page preserves the detailed work and its failures.

The globe with the specified field has the lowest fit cost in all 53 selected
NASA stretches under both processing assumptions. Aircraft uncertainty remains
open. The [current milestones](ANALYSIS_ROADMAP.md#current-milestones-and-finish-line)
prioritize matched field and gyro controls before a bounded NASA pilot. The
sections below preserve earlier development, including failed gates.

The [portable whole-period replay](prediction-simultaneous-law-family-v3/REPLAY.md)
reproduces the 96-recording v3 report exactly from its frozen sources and
saved evidence. The 95/96 simulated result and its 4.85% upper failure bound
remain separate from aircraft prediction uncertainty.

The [isolated NASA refit](ilvis0-matched-trial-observed-runtime/refit-evidence/README.md)
reproduced one recorded IMU8 training fit and its native builds byte for byte.
The run hit its wall limit before forecasting. A
[separate replay](ilvis0-matched-trial-observed-runtime/forecast-evidence/README.md)
then reproduced all 223 later positions using the saved fit.

The [carrier-phase pilot](ilvis0-measurement-contribution/GPS_CARRIER_PHASE_RESULT.md)
recovered 1,109 of 1,110 GPS displacements and found that onboard positions
best agreed with phase-derived vertical motion on both recordings.
The [matched force check](ilvis0-measurement-contribution/GPS_CARRIER_FORCE_RESULT.md)
then preserved the globe–disc force ordering across all 991 windows and both clocks.
The [two-sided force calibration](ilvis0-measurement-contribution/FORCE_INTERVAL_CALIBRATION_RESULT.md)
found that one nonnegative gain left a measurable gap in all 24 profiles.
The [trajectory-order comparison](ilvis0-measurement-contribution/FORCE_PATH_ORDER_RESULT.md)
improved the height fit on the same windows and left a force gap in every profile.
The [packet-direction check](ilvis0-measurement-contribution/FORCE_DIRECTION_GAP_RESULT.md)
quantified the peak force direction change needed to account for those gaps.
The [axis-calibration pilot](ilvis0-measurement-contribution/AXIS_FORCE_PILOT_RESULT.md)
then checked 32 signed gain and offset proposals on the original counts.
All left training gaps.
The [checked nonlinear updates](ilvis0-measurement-contribution/EXACT_AXIS_FORCE_RESULT.md)
reduced all 32 training gaps and 28 later gaps. None reached zero.
The [paired receiver comparison](ilvis0-measurement-contribution/PAIRED_RECEIVER_FORCE_RESULT.md)
found that receiver choice can shift predicted force by as much as the
smaller gaps on fourth-degree paths.
The [ESA changing-drift check](prediction-observed-development/ESA_CHANGING_DRIFT_TRANSFER_RESULT.md)
put the later receiver positions inside all 20 forecast ranges under both
receiver assumptions. The model ranges overlapped throughout the later period.
The [correction audit](prediction-observed-development/ESA_DRIFT_CORRECTION_AUDIT_RESULT.md)
traces the kilometre-scale correction to a high-order inertial drift term.
[Removing that term](prediction-observed-development/ESA_NO_SNAP_ABLATION_RESULT.md)
restored some shape separation on the same development flight.
The [generated backcheck](prediction-observed-development/ESA_NO_SNAP_GENERATED_BACKCHECK_RESULT.md)
found that the narrower law missed 59 of 256 saved histories.
The [correlated whole-path score](prediction-observed-development/ESA_JOINT_PATH_SCORE_RESULT.md)
retains the specified-field globe preference in both complete ESA settings
under either law.
The [known-model replay](prediction-observed-development/MATCHED_GENERATED_JOINT_SCORE_RESULT.md)
recovers 9–12 of 12 generating labels across the four error assumptions.
The [provisional decision rule](prediction-observed-development/JOINT_SCORE_ABSTENTION_RESULT.md)
made six correct shape calls in the 12 development histories and abstained
on both route controls and all four ESA settings.
The [matched flight-group score checks](PREDICTION_GROUP_DECISION.md) use the
existing rank and cohort rules with fixed reference IDs. In a software replay,
all twelve generated histories abstain at 5% because the reference sets are
too small. This check does not calibrate the full aircraft procedure.
A [cheaper reference calculation](PREDICTION_GROUP_DECISION.md#a-cheaper-reference-test)
passes known-answer checks using only the generating model for each
reference. The query still uses all three models. Aircraft calibration
and the ability to separate the models remain open.
The [affine scale check](prediction-observed-development/CALIBRATED_JOINT_SCORE_RESULT.md)
accounts for fitted calibration and a shared change in error scale. It shows
why a receiver change after the training cut needs its own check.
The [ESA scale sensitivity check](prediction-observed-development/JOINT_SCORE_SCALE_WINDOW_RESULT.md)
finds different adequacy ranges for the two receiver weightings on the same
sealed forecasts. The original decision remains an abstention.
The [equal-horizon scale transfer](prediction-observed-development/ESA_ROLLING_SCALE_TRANSFER_RESULT.md)
finds 3.31–3.70 times as much squared standardized error later in the same
flight. The earlier scale leaves every model outside the provisional later
reference limit.
The [smooth-error diagnostic](prediction-observed-development/FORECAST_SMOOTH_ERROR_RESULT.md)
finds that constant through cubic changes explain at most 1.23% of the
later weighted score. The increase persists after those trends are removed.
The [paired forecast check](prediction-observed-development/FORECAST_PAIR_INFORMATION_RESULT.md)
finds that at least 86% of the squared path separation survives the same
smooth-error allowance. It measures ideal separation on fixed paths.
The [alternate-training forecast check](prediction-observed-development/FORECAST_FAMILY_MARGIN_RESULT.md)
retains at least 99.1% of the distance when independently varying the
receiver training export across each model's saved forecasts.
The [contrast error check](prediction-observed-development/MODEL_CONTRAST_PARTITION_RESULT.md)
separates ranking evidence from common forecast error. One error law
ranks every generated case correctly but exceeds the nominal contrast
error limit on 10/12 known-model paths.
The [split-window control](prediction-observed-development/SPLIT_CONTRAST_RESULT.md)
checks a directional reference with separate calibration data. Reusing
those data to choose the direction gives excessive apparent error
even under the correct generated law.
The [ESA training-window check](prediction-observed-development/TRAINING_WINDOW_GEOMETRY_RESULT.md)
finds that a split retains numerical rank but loses nearly all information
in the weakest calibration combination on the opened flight.
The [generated direction-transfer check](prediction-observed-development/FORECAST_DIRECTION_TRANSFER_RESULT.md)
finds that borrowing two directions from the other route retains a
median 20% of the weakest model contrast. Donors on the same route
retain more information, with substantial variation.
The [wider direction preflight](prediction-observed-development/WIDE_DIRECTION_PREFLIGHT_RESULT.md)
retains at least 97.1% of separation on separate generated route
controls, but weak forecast pairs miss the illustrative power benchmark
even when the exact best direction is known.
The [training-route check](prediction-observed-development/RECEIVER_ROUTE_INFORMATION_RESULT.md)
finds different strengths for shape and field on the three selected
ESA windows using receiver data alone and a declared offset range.
The [receiver motion precision check](prediction-observed-development/RECEIVER_MOTION_PRECISION_RESULT.md)
shows that those windows need substantially tighter motion constraints
than the course and climb proxies supply under reported receiver errors.
The [native ESA forecast replay](prediction-observed-development/ESA_NATIVE_TANGENT_REPLAY_RESULT.md)
recovers all 27 calibration derivatives from one exact saved forecast
and shows how weakly constrained training directions grow on the later path.
The [finite-change check](prediction-observed-development/ESA_TANGENT_REMAINDER_RESULT.md)
compares six changes within the original calibration bounds and shows where
the linear approximation begins to lose accuracy.
The [three-model calibration check](prediction-observed-development/ESA_MIXED_CALIBRATION_RESULT.md)
measures the extra forecast change from combining calibration shifts and
shows why shifts of the same size can have very different earlier fit costs.
The [earlier-cost check](prediction-observed-development/ESA_EARLIER_FIT_COST_RESULT.md)
matches the approximate increase in earlier loss. Receiver white noise
alone gives too wide a bound to certify any of the six exact cost changes.
The [original-weight replay](prediction-observed-development/ESA_ORIGINAL_WHITENING_RESULT.md)
scores those six steps directly and preserves the training weights for
future checks.
The [calibration contrast check](prediction-observed-development/ESA_CALIBRATION_CONTRAST_RESULT.md)
bounds how far calibration can move each raw forecast toward its
competitors under the same earlier-fit allowance.
The [conditioned calibration comparison](prediction-observed-development/ESA_CONDITIONED_CALIBRATION_RESULT.md)
repeats that test after accounting for correlation with earlier receiver
positions and checks the selected steps by exact propagation.
The [native future-error sensitivity](prediction-observed-development/ESA_NATIVE_FUTURE_ERROR_RESULT.md)
tests how much added receiver scatter or drift would be needed to explain
the three forecasts' misses on a previously scored development interval.
The [native forecast transfer check](prediction-observed-development/ESA_NATIVE_ROLLING_TRANSFER_RESULT.md)
finds four times the squared standardized error at the later of two
equal-length held-out windows on the same flight.
The [later-error motion check](prediction-observed-development/ESA_INNOVATION_TRANSFER_RESULT.md)
locates most of the east-ordered score after a turn and tests whether
more detailed estimates from the earlier window improve transfer.
The [straight-flight and heading-step checks](prediction-observed-development/ESA_MANEUVER_ERROR_RESULT.md)
find substantial height drift during straight flight and little
evidence that a lasting heading step explains the turn-associated error.
The [motion-dependent error check](prediction-observed-development/ESA_MOTION_ERROR_LAW_RESULT.md)
tests separate covariance shapes for persistent acceleration and a
transient maneuver response against the original saved forecasts.
The [component preflight](prediction-observed-development/ESA_COMPONENT_PREFLIGHT_RESULT.md)
finds that the first forecast cannot constrain maneuver error, and
locates the motion needed to test it in two preselected training windows.
The [known-answer scale check](prediction-observed-development/COVARIANCE_SCALE_CONTROLS.md)
recovers separate error scales on generated samples and abstains when
the data cannot distinguish them.
The [fitted-path control](prediction-observed-development/FITTED_PATH_COVARIANCE_CONTROLS.md)
checks training-only estimates with correlated errors across the split.
The [saved ESA design check](prediction-observed-development/ESA_FITTED_SCALE_SUPPORT_RESULT.md)
finds that calibrating one flight absorbs more than 99.5% of the proposed
steady error pattern for each Earth model.
The [bounded replay](prediction-observed-development/ESA_BOUNDED_DRIFT_RESULT.md)
finds that the existing limits leave less than 1% of each steady test
pattern, and fixing accelerometer biases and gravity still leaves less
than 1.4%.
The [two-ground-stop check](prediction-observed-development/ESA_GROUND_FORCE_SUPPORT_RESULT.md)
finds that the accelerometer vectors are nearly parallel. Even exact
knowledge of both magnitudes would do little to separate steady drift
from calibration in the archived flight interval.
The [receiver-velocity check](prediction-observed-development/ESA_RECEIVER_ACCELERATION_RESULT.md)
shows stronger maneuvers in the selected training windows, with printed
covariance too large to resolve the working steady-drift scale from
individual receiver velocity derivatives.
The [matched position check](prediction-observed-development/ESA_POSITION_ACCELERATION_RESULT.md)
reduces the reported uncertainty substantially. Differences between
averaging widths remain larger than the working steady-drift scale.
The [matched force check](prediction-observed-development/ESA_MATCHED_FORCE_RESULT.md)
applies the same time weights to the raw accelerometer and the receiver
path. A single offset transfers poorly to one of the three windows.
The [fast-variation check](prediction-observed-development/ESA_FORCE_VARIATION_RESULT.md)
finds that averaging vectors over 0.1 seconds first reduces that window's
disagreement from 0.065 to 0.00090 m/s² RMS after offset correction.
The [sealed forecast comparison](prediction-observed-development/ESA_FAST_FORCE_TRANSFER_RESULT.md)
finds that allowing the same variation to scale prediction errors
worsens the later log score under both archived error descriptions.
The [error-shape transfer check](prediction-observed-development/ESA_ERROR_SHAPE_TRANSFER_RESULT.md)
finds that a correction estimated from earlier errors greatly reduces
later height drift in straight flight. A turn response better explains
the later east error in the short turning forecast.
The [repeat-turn inventory](prediction-observed-development/ESA_REPEAT_TURN_RESULT.md)
finds four receiver-selected forecast supports outside the previously
scored or preselected windows. A known-answer check verifies how changed
drift and a reversed turn response appear in the later position scores.
The [repeat-turn input preflight](prediction-observed-development/ESA_REPEAT_TURN_INPUT_RESULT.md)
verifies the exact receiver/IMU timing on all four supports and binds
training inputs without decoding later receiver positions.
The [repeat-turn scoring qualification](prediction-observed-development/ESA_REPEAT_TURN_SCORING_RESULT.md)
checks the forecast seal and the four fixed covariance choices against
generated data. Aircraft trajectory fitting remains a separate step.
The [prepared forecast inputs](prediction-observed-development/ESA_REPEAT_TURN_MATERIAL_RESULT.md)
verify all 12 files for the four windows, with later receiver positions
held outside the forecast worker inputs.
The [repeat-turn forecast release](prediction-observed-development/ESA_REPEAT_TURN_RELEASE_RESULT.md)
binds those inputs to 16 finite fit tasks with reboot recovery. It
verifies the forecast choices before opening later receiver positions.
All 16 fits passed. The [scored forecasts](prediction-observed-development/ESA_REPEAT_TURN_FORECAST_RESULT.md)
have 0.44–1.97 m three-dimensional RMS position error across four turns
on the development flight. The turn allowance improved every score,
and adding both allowances gave the best score in three windows.
In a [saved-score diagnostic](prediction-observed-development/esa-repeat-turn-scale-diagnostic.json),
scaling the combined allowance on three windows improved two of four
omitted-window scores. The other two scores worsened. Reproduce the check
with the numerical guard on one thread and the module
`lll.esa_repeat_turn_scale_diagnostic`. It reads only the two saved score
receipts and makes zero fits.
The [training-scale comparison](prediction-observed-development/esa-repeat-turn-training-scale-diagnostic.json)
instead used each forecast's own earlier residuals. Every later score
worsened. Run `lll.esa_repeat_turn_scale_diagnostic --training` to verify
the result from the archived fit and score receipts.
The [shape check](prediction-observed-development/esa-repeat-turn-covariance-shape-diagnostic.json)
still favors the turn allowance in all four windows after giving each
covariance its best overall scale on the same scored positions. Use
`lll.esa_repeat_turn_scale_diagnostic --profile` to reproduce this
retrospective check from the score receipts.
The [steady-course control inventory](prediction-observed-development/ESA_STRAIGHT_CONTROL_PLAN.md)
finds four disjoint same-flight comparison windows using GPS course only.
The recording's clocks passed on all four. The
[input preparation](prediction-observed-development/ESA_STRAIGHT_CONTROL_MATERIAL_PLAN.md)
is frozen with a one-thread allowance and five passing workflow checks.
Its manifest SHA-256 is
`cbf50b32601176804dca47a43dd2712128b2536a205ae642eda2381520f19622`.
The preparation passed. It verified all 12 input files, including the
training positions and all query times, while leaving later positions withheld.
The [control forecast worker](prediction-observed-development/ESA_STRAIGHT_CONTROL_FORECAST_PLAN.md)
reuses the turn study's conditional forecast and covariance code. The
[release and comparison checks](prediction-observed-development/ESA_STRAIGHT_CONTROL_RELEASE_PLAN.md)
include a [timing control](prediction-observed-development/ESA_STRAIGHT_CONTROL_TIMING_CHECK.md)
that reapplies each archived turn's angular exposure to its matched
steady-course forecast. Seven software checks passed. The control fits
used the verified input files in the separately frozen forecast study.
The [steady-course results](prediction-observed-development/ESA_STRAIGHT_CONTROL_RESULT.md)
record all 16 passing fits and eight forecasts scored against later
GPS positions. Their 3D RMS errors were 0.17–0.73 m. A steady-flight
allowance improved all scores. Assigning the matching turn exposure
to each steady window worsened every score.
The [same-flight scale check](prediction-observed-development/ESA_COMMON_SCALE_CHECK.md)
found no single covariance multiplier compatible with all error sizes
under a simultaneous Gaussian reference. This held in each motion category.
The [held-pair covariance check](prediction-observed-development/ESA_COMPONENT_SCALE_TRANSFER_RESULT.md)
finds no improvement in the reference count with a fitted common scale.
The separate-scale optimizer meets its stopping rule in one of eight
checks. Both windows scored with that fit miss the reference.
The [native-whitened replay](prediction-observed-development/ESA_WHITENED_SCALE_TRANSFER_RESULT.md)
verified equivalent scores and left the optimizer count at one of eight.
The [full variance-range check](prediction-observed-development/ESA_COMPONENT_SCALE_FEASIBILITY_RESULT.md)
rules out a common set of the three variance scales on the same eight
windows under the working error reference.
The [axis and time check](prediction-observed-development/ESA_FORECAST_ERROR_LOCALIZATION_RESULT.md)
finds that each axis of the hardest turn exceeds the full-path limit,
even after allowing both added covariance terms.
The [motion-dependent innovation check](prediction-observed-development/ESA_MOTION_INNOVATION_SCALE_RESULT.md)
improves six of eight held-out log scores and leaves the reference count
at one of eight. All comparisons reuse the same development flight.
The [separate quiet scale check](prediction-observed-development/ESA_AXIS_INNOVATION_SCALE_RESULT.md)
improves every held-out log score against the shared motion rule, with two
of eight windows inside the error reference. Both new rules miss the screen.
The [continuous range check](prediction-observed-development/ESA_AXIS_SCALE_COMPATIBILITY_RESULT.md)
finds a setting that covers all four steady windows. The separate search over
steady and turn windows leaves part of the allowed scale range unresolved.
The [continuous reference transfer](prediction-observed-development/ESA_SCALE_REFERENCE_TRANSFER_RESULT.md)
puts every donor window inside the reference and only three of eight omitted
windows inside. The worst omitted score exceeds twice the upper reference.
The [smooth position error check](prediction-observed-development/ESA_SCORED_PATH_SHAPE_RESULT.md)
accounts for 82% of the largest steady-window joint error with nine smooth
terms but leaves a large spread in the remaining turn errors.
The [matched path check](prediction-observed-development/MATCHED_SHAPE_DRIFT_RESULT.md)
finds that the same nine smooth terms can absorb over 99.9% of the squared
separation between globe and disc on each of four same-field forecast pairs.
Absorbing the entire smooth part would take a 69.50–1,441.19 m RMS
difference between the corrections for the two candidates.
For one exact ESA pair, conditioning on earlier positions removed most
of the smooth difference while leaving about 0.76 m RMS outside the
smooth terms under either set of forecast means.
The [boundary check](prediction-observed-development/SHAPE_FORECAST_BOUNDARY_RESULT.md)
retained at least 98.9% of the squared weighted shape separation after
omitting the first 20 later report times.
The [local calibration bound](prediction-observed-development/CONDITIONED_SHAPE_CALIBRATION_RESULT.md)
leaves at least 98.28% of the weighted shape distance in one setting.
It uses the two archived derivative arrays and supplies an affine bound
under the original local parameter and earlier fit-loss allowances.
The [nonlinear error targets](prediction-observed-development/SHAPE_REMAINDER_HEADROOM_RESULT.md)
show what a full-region proof would have to establish. An earlier
remainder norm of 0.1 per candidate leaves 12.78 standardized units
for their combined later remainder in the shape direction.
The [exact probe replay](prediction-observed-development/SHAPE_REMAINDER_WITNESS_RESULT.md)
found a counterexample to that earlier limit over the full box. Both
near-limit probes that pass the original loss check had much smaller
remainders. The result motivates a proof on the actual feasible region.
The [directional error conversion](prediction-observed-development/SHAPE_REMAINDER_METRES_RESULT.md)
traces both early and late position errors through the working covariance.
It gives a sufficient 4.03 cm coordinate limit for the later score, subject
to the separate earlier standardized error limit of 0.1.
The shared-prefix predictor now includes the archived gravity adjustment.
The generated tests check each model at three query times. The full-flight
error bound remains open.
The [future covariance control](prediction-observed-development/FUTURE_COVARIANCE_BRACKET_RESULT.md)
checks forecasts under a range of later receiver error and drift. It
enclosed all 768 generated scores within that range. Aircraft bounds
remain open.
The [bounded whole-path check](prediction-observed-development/BOUNDED_JOINT_PATH_RESULT.md)
agrees with an independent calculation on 256 affine paths. It tests whether
one calibration can explain both periods and requires a bound on nonlinear
prediction error before aircraft use.
The [companion receiver forecast check](ilvis0-measurement-contribution/COMPANION_FORECAST_RESULT.md)
kept the same ranking of the three saved IMU8 forecasts at every horizon,
including when scored directly against the second receiver's positions.
In a [separate four-group check](prediction-group-transfer/COMPANION_RECEIVER_RESULT.md),
switching receivers after an earlier offset adjustment changed later height
RMS by at most 0.32 m on shared epochs. Every overlap ended before its forecast did.

The matched-field software controls now exercise the counted fitting and
withheld forecast path for four geometry and field combinations. One
gyro-free control shares the accelerometer calibration over every
receiver-selected window and preserves the remaining attitude ambiguity.
The [three-sample motion check](ilvis0-measurement-contribution/FORCE_MOTION_TRIPLETS.md)
can detect when two individually possible steps require incompatible middle orientations.
The [whole-history extension](ilvis0-measurement-contribution/FORCE_MOTION_HISTORY.md)
detects a conflict missed by every overlapping triple and verifies complete
paths when the supplied directions and limits allow a grid witness.
On [two saved development recordings](ilvis0-measurement-contribution/RECORDED_MOTION_RATE_RESULT.md),
the four candidates' rate brackets overlapped in all 16 matched settings.
The longer [generated field and offset study](ilvis0-measurement-contribution/MATCHED_GENERATED_RESULT.md)
then completed all 128 planned fits. The 32 truth-matched fits passed, and
12 of 32 settings finished all four candidates. The result retains the
unresolved alternative fits and starts no NASA pilot.

The [fixed-point precision check](ilvis0-measurement-contribution/MATCHED_PRECISION_RESULT.md)
replayed both the endpoint and proposed correction of all 33 unfinished
fits. Wider arithmetic brought 31 cost changes within the original limit.
Two still exceeded it. The replay charged 132 calls, with no refits or
changes to the original stopping results.

The [prospective wider solver check](ilvis0-measurement-contribution/MATCHED_WIDE_RESULT.md)
completed 15 of 16 four-model comparisons on fresh generated histories,
up from six with binary64. All 16 known-truth fits passed withheld accuracy.
The result qualifies the generated comparison and leaves one setting
unfinished.
The [saved solver trace audit](ANALYSIS_ROADMAP.md#dependency-ordered-backlog)
found that 559 wider training evaluations spent time computing derivatives at
trials the solver rejected. It started no new fits.

The [pilot metadata audit](ilvis0-measurement-contribution/MATCHED_PILOT_ELIGIBILITY.md)
joined all 53 stretches to the saved decoder, GPS and provenance records.
Twenty-one stretches meet the saved checks, spanning 18 flight groups.
All are southern. The audit did not select any pilot recordings.
The [northern clock check](ilvis0-measurement-contribution/NORTHERN_IMU21_CLOCK_RESULT.md)
cleared two saved decoder failures under nominal timing. The original two-date
failure and resulting eligibility restriction remained.
The [southern pilot reservation](ilvis0-measurement-contribution/MATCHED_PILOT_CANDIDATES_RESULT.md)
then fixed four candidate groups using metadata alone, with two recorders
of each type and both available course sectors.

The [GPS window uncertainty control](ilvis0-measurement-contribution/SUPPORT_POLICY.md#first-known-answer-results)
reproduced four known force predictions and carried both plausible windows
through the calculation when a smooth generated height error changed the
selection. It preserved shared receiver errors across windows and models.

The [shared-calibration control](ilvis0-measurement-contribution/SUPPORT_POLICY.md#shared-accelerometer-calibration)
preserved all eight known moving cases with gyro data omitted. It also
excluded a constructed case where every target could be matched individually
but no single accelerometer calibration worked across the history.

The [shared GPS height-error check](ilvis0-measurement-contribution/SHARED_GPS_ERROR_RESULT.md)
applied an illustrative smooth 10 cm error to 919 saved windows. It
changed individual force estimates and did not reverse the same-field
globe–disc force difference at any tested phase.

The [raw GPS coverage preflight](ilvis0-measurement-contribution/GPS_RECONSTRUCTION_PREFLIGHT_RESULT.md)
matched satellite records to all 48,099 selected receiver epochs. L1 range
geometry passed at every epoch across 21 sources. This qualifies input
availability for a separate GPS position calculation.

The [two-flight GPS reconstruction](ilvis0-measurement-contribution/GPS_RECONSTRUCTION_PILOT_RESULT.md)
closed all 2,224 position solutions. Its separately processed positions
showed much smaller vertical acceleration disagreement with onboard GPS
when calculated over 30 seconds than over 10 seconds.

The [same-window GPS force comparison](ilvis0-measurement-contribution/GPS_FORCE_COMPARISON_RESULT.md)
kept the same-field globe–disc force ordering across all 3,213 supported
windows under three GPS processing methods. It shows which parts of the
force comparison are sensitive to the position source.

The [matched inertial input check](ilvis0-measurement-contribution/MATCHED_OBSERVED_INPUTS_RESULT.md)
verified both clock conventions at all 1,111 shared receiver epochs.
It preserved original packet counts and separated 740 training
positions from 371 later scoring positions.
The [force-window audit](ilvis0-measurement-contribution/SUPPORT_POLICY.md#keeping-training-and-later-force-windows-separate)
found 680 training and 311 later 30-second windows using fixes entirely
on their own side of the split. Sixty crossed the split.

The [common accelerometer support check](ilvis0-measurement-contribution/MATCHED_FORCE_SUPPORT_RESULT.md)
retained whole packets under both clocks in all 991 eligible windows and
measured the count-rounding and clock effects without using gyro values.

The [matched force averages](ilvis0-measurement-contribution/MATCHED_FORCE_AVERAGE_RESULT.md)
kept both shape signs across 5,946 window, clock and GPS choices. The
[training-only gain check](ilvis0-measurement-contribution/MATCHED_FORCE_GAIN_RESULT.md)
cleared all training lower bounds below 1% correction. All four IMU21
candidates passed the later check, while every IMU8 candidate had violations.

The [shared GPS covariance check](ilvis0-measurement-contribution/MATCHED_FORCE_COVARIANCE_RESULT.md)
kept errors common to the four models and the overlapping force windows.
Under its assumed law the largest later onboard lower-bound violation was
about 0.225 of a projected standard deviation.

The [two-recording numerical preflight](ilvis0-measurement-contribution/MATCHED_OBSERVED_NUMERICAL_RESULT.md)
verified six later forecasts and their stopping checks. A zero-field disc
fit failed its stopping check, and the other was unstarted at the time limit.
The [continuation](ilvis0-measurement-contribution/MATCHED_UNSTARTED_DISC_RECOVERY_RESULT.md)
passes the sole unstarted IMU21 fit and verifies all four forecasts on its
148 later GPS reports. Globe has lower 3D error at both matched fields.
The [shared GPS reference check](ilvis0-measurement-contribution/MATCHED_IMU21_RECEIVER_HULL_RESULT.md)
preserves both 3D orderings and the disc's height advantage at zero field
throughout the observed receiver spread.
The [saved trace check](ilvis0-measurement-contribution/MATCHED_REPEATED_TRIAL_RESULT.md)
finds seven repeated full proposals in the original IMU8 stopping failure.
In the [eight generated fit checks](ilvis0-measurement-contribution/MATCHED_REUSE_GENERATED_RESULT.md),
reusing exact rejected proposals cuts training evaluations from 282 to 239
with identical stopping outcomes, final costs and later predicted positions.
The [recorded controls](ilvis0-measurement-contribution/MATCHED_REUSE_OBSERVED_RESULT.md)
also pass with exact agreement. Each takes the same number of evaluations
as its saved reference because neither has a duplicate rejection.
The [GPS extension](ilvis0-measurement-contribution/GPS_RECONSTRUCTION_EXTENSION_RESULT.md)
adds 2,248 converged position solves from two separate flight groups.
The vertical acceleration differences fall by factors of 8 to 12 when
the time window goes from 10 to 30 seconds.
The [packet alignment](ilvis0-measurement-contribution/MATCHED_EXTENSION_INPUTS_RESULT.md)
matched all 1,123 original receiver reports to both GPS reconstructions
and checked both clocks. The 375 later positions are saved separately.
All [eight added forecasts](ilvis0-measurement-contribution/MATCHED_EXTENSION_FORECAST_RESULT.md)
pass. The [four-flight audit](ilvis0-measurement-contribution/MATCHED_FOUR_GROUP_AUDIT_RESULT.md)
finds lower 3D error for globe in all complete same-field pairs and a
fixed accuracy pass for specified-field globe on three of four flights.
The [shared GPS check](ilvis0-measurement-contribution/MATCHED_EXTENSION_RECEIVER_HULL_RESULT.md)
holds the 3D rankings and the absolute accuracy passes across the measured
receiver spread on both added flights.
The [force-only follow-up](ilvis0-measurement-contribution/MATCHED_EXTENSION_FORCE_RESULT.md)
checks 1,003 windows without using gyro values. All four IMU21 candidates
clear the necessary force inequality, while three IMU8 candidates have
small later gaps. The result leaves model selection open.
One [shared GPS perturbation](ilvis0-measurement-contribution/MATCHED_EXTENSION_FORCE_WITNESS_RESULT.md)
clears all 79 gaps on the added IMU8 flight and preserves the full-IMU
rankings on all three GPS references.
All eight [gyro-free calibration controls](ilvis0-measurement-contribution/GYRO_FREE_CALIBRATION_CONTROLS_RESULT.md)
predict the generated later force correctly under both clocks. A separate
calculation bounds the packet-averaging error for a stated limit on how
fast the force changes within a packet.
The [adjacent-packet check](ilvis0-measurement-contribution/PACKET_FORCE_CHANGE_RESULT.md)
uses the recorded accelerometer averages to reject some small force-change
limits. Both clocks give similar results under the same error allowances.
The [paired accelerometer comparison](ilvis0-measurement-contribution/PAIRED_ACCELEROMETER_RESULT.md)
measures how the difference between two recorders shrinks as averaging time
increases on two NASA flight legs. It leaves absolute instrument error open.
The [accelerometer gain-range check](ilvis0-measurement-contribution/FORCE_GAIN_RANGE_RESULT.md)
shows that all four candidates can clear the saved force-only checks at gains
the earlier data allow. It measures the remaining predicted force differences.
[Paired gyro timing](ilvis0-measurement-contribution/PAIRED_GYRO_CLOCK_RESULT.md)
compares four original recorders on two overlapping tracks using whole
packets. Shifts fitted on earlier data change later gyro disagreement by less
than 5% at the fitted window lengths. Both tasks completed without any new
Earth-model fits.

The [paired mounting-separation check](ilvis0-measurement-contribution/PAIRED_LEVER_ARM_RESULT.md)
reduced the mixed pair's one-second vector RMS by about 15%. The fitted
displacements changed with averaging width and do not establish mount geometry.

The [paired check on the original force windows](ilvis0-measurement-contribution/PAIRED_FORCE_WINDOW_RESULT.md)
shows how much uncertain packet edges can change the recorder comparison.

The [receiver-spread replay](ilvis0-measurement-contribution/MATCHED_FORECAST_RECEIVER_RESULT.md)
kept the same-field globe forecast advantage inside the three-GPS hull at
every tested horizon. The full-record lower horizontal errors were 19.19 m
and 2.03 m.

The [saved aircraft point check](ilvis0-measurement-contribution/MATCHED_TRIAL_PROBE_RESULT.md)
found exact agreement between the value-only and tangent calculations on all
four points and measured CPU time for each. No fit was restarted.

The [full generated trial check](ilvis0-measurement-contribution/MATCHED_TRIAL_FITS_RESULT.md)
reproduced eight complete solver and forecast records, including one failed
stop, while cutting the number of full tangent calls from 290 to 127.

The [recorded trial check](ilvis0-measurement-contribution/MATCHED_TRIAL_OBSERVED_RESULT.md)
reproduced both IMU8 solver records and the available forecast. The original
failed stop stayed failed and required 18 fewer full tangent calls.

The [twenty-group retrospective forecast extension](prediction-group-transfer/REMAINING_GROUPS_PREDICTION_RESULT.md)
completed 80 planned fits across 20 additional recording groups. Thirty fits
passed numerical checks. Nine groups have a usable later forecast within the
fixed earlier development reference and pass the separate physical screen;
eleven lack a usable later-cut fit. Five groups pass both earlier-cut checks;
four of the nine scored groups pass the later cut only. This is a one-model
development forecast check on the same archive, with all failures preserved.
Its [saved stopping audit](prediction-group-transfer/REMAINING_GROUPS_STOPPING_AUDIT.md)
shows that 49 nonpassing fits failed the fresh cost-change check and one
failed initial stationarity. None reached the evaluation ceiling or failed
the actual-position limits. This diagnosis does not reclassify any fit.
The [saved correction reconstruction](prediction-group-transfer/REMAINING_GROUPS_CORRECTION_DIAGNOSTIC.md)
matches all 49 failed probes' predicted changes without a new native call.
Thirty-one locally predict a cost change below the frozen limit while their
fresh checks failed. A [separate three-case forecast sensitivity check](prediction-group-transfer/CORRECTION_FORECAST_RESULT.md)
compared later predicted paths after those saved corrections. Its first
source-freeze attempt stopped before calculation; the repaired study
completed three charged forecasts. Maximum horizontal path differences were
0.038 mm, 0.052 mm and 16.3 mm. This does not score prediction accuracy or
change any of the 50 original failed-fit labels.
The [saved later-error audit](prediction-group-transfer/REMAINING_ERROR_STRUCTURE.md)
retains the eleven unscorable groups and describes signed errors, trends and
adjacent-epoch correlations in the nine scored later forecasts. Median RMS
errors are 1.04 m north, 0.69 m east and 4.43 m in height. It adds error-law
diagnostics without another fit or a coverage claim.
The [generated solver forecast control](prediction-group-transfer/GENERATED_SOLVER_FORECAST_RESULT.md)
then fit 24 short independent known-answer cases across all three models, two
clock constructions, two bounded solvers and two starts. All 24 passed
numerical stopping and all six four-fit forecast-agreement gates passed.
The largest later-path spread was 2.44×10⁻⁷ m. This qualifies only the
short six-parameter software control, not the 26-parameter archive fit or
aircraft prediction coverage.
The [full-calibration generated pilot](prediction-group-transfer/FULL_CALIBRATION_SOLVER_RESULT.md)
used one 60-second noisy known-answer flight, all 26 calibration directions,
two stopping-provider paths sharing one optimizer and two starts. Its real-worker preflight and all four
fits completed; 4/4 passed numerical stopping and the generated physical
screen. The four later paths agreed within 3.42×10⁻⁷ m, while later
horizontal and height errors against truth were about 0.32 m and 1.31 m.
The first preflight's thread-environment mismatch remains a separate sealed
technical failure with zero native calls. This is development evidence on
one generated history, not an observed aircraft decision.
The [multimodel full-calibration control](prediction-group-transfer/MULTIMODEL_SOLVER_RESULT.md)
then completed 24/24 generated fits across all three models, two Z-gyro
calibration settings, both bounded solvers and both starts. All six four-fit
forecast-agreement gates and all 24 generated physical screens passed; the
maximum later-path spread was 9.17×10⁻⁷ m. Its six fixtures share one
declared noise seed. It does not revise the 50 nonpassing aircraft fits or
calibrate aircraft prediction coverage.
The [nominal 200 Hz generated solver control](prediction-group-transfer/NOMINAL_200HZ_SOLVER_RESULT.md)
closed 24/24 fits and all six four-fit forecast-agreement gates under six
distinct noise seeds. All 24 passed the generated physical screen; the
greatest within-fixture later-path spread was 1.3×10⁻⁵ m. This is an
exact-grid software result, not a test of irregular packet-header timing or
aircraft prediction coverage.
The [longer generated solver confirmation](prediction-group-transfer/LONG_HORIZON_SOLVER_RESULT.md)
then passed 24/24 fits and all six preregistered forecast and training-cost
agreement gates on 120-second histories under both clock policies. Its
maximum within-case later-path spread was 5.06×10⁻⁵ m. The
[saved twenty-group two-start audit](prediction-group-transfer/REMAINING_PAIR_AGREEMENT.md)
then compared the earlier development study's 40 forecast pairs without new
fits: all 40 were within 0.1 m, with a maximum difference of 6.03 mm. Only
30/80 original fits passed their stopping checks; those labels remain fixed.
Neither result establishes observed-aircraft forecast accuracy or coverage.
The [solver-independence correction](prediction-group-transfer/SOLVER_INDEPENDENCE_ERRATUM.md)
records that the generated fit providers share one bounded trust-region
optimizer. Their two-start and stopping-wrapper results stand, but an
independent optimizer comparison remains open.
The [independent bounded-optimizer control](prediction-group-transfer/INDEPENDENT_SOLVER_RESULT.md)
then compared SciPy TRF with the trust-region optimizer on six short
generated model/clock histories. All 24 fits passed final stopping and
generated physical screens; all six predeclared cost/withheld-path gates
passed. The greatest within-case path spread was 5.06×10⁻⁵ m. This closes
the method-diversity gap for the short generated control. Observed aircraft
still need separate method and prediction checks.
The [120-second distinct-optimizer study](prediction-group-transfer/LONG_INDEPENDENT_SOLVER_RESULT.md)
then passed 24/24 numerical stops, 24/24 generated physical screens and all
six cost/path agreement gates. Its largest within-history later-path spread
was 3.67×10⁻⁵ m. A host interruption left two charged starts unfinished and
two tasks unstarted; the [finite continuation](prediction-group-transfer/INDEPENDENT_METHOD_RUNBOOK.md)
completed those four identities without repeating the 20 sealed results.
This qualifies the generated numerical control. A separate
[one-fit SciPy preflight](prediction-group-transfer/OBSERVED_METHOD_V2_PREFLIGHT.md)
on a preselected recorded input passed its technical wiring check but did
not converge under its 30-call cap. The
[24-fit observed method comparison](prediction-group-transfer/OBSERVED_METHOD_PILOT_V2_RESULT.md)
completed without worker errors, but only 7/24 fits met their numerical
stopping checks and 4/6 matched sets met the development path-agreement
scale. The [saved-result diagnosis](prediction-group-transfer/OBSERVED_METHOD_V2_DIAGNOSIS.md)
shows why the checks failed. This does not qualify the method; aircraft
prediction accuracy and calibrated evidence remain open. A later
[eight-endpoint timing check](prediction-group-transfer/OBSERVED_FIXED_ENDPOINT_RESULT.md)
charged all 80 calls, replayed all eight points exactly, and found close
timing derivatives even when probe steps crossed packet intervals. It did not
refit the recorded data or alter any stopping label.
The [fixed calibration-swap study](prediction-group-transfer/OBSERVED_CALIBRATION_SWAP_RESULT.md)
then completed 24/24 declared vectors and all baseline/full-vector controls.
Individual parameter-group swaps usually worsen training fit sharply;
different fitted groups compensate one another. The large hybrid forecast
shifts are diagnostics, not viable alternate fits or Earth-model evidence.
The [complete-vector path study](prediction-group-transfer/OBSERVED_PAIR_PATH_RESULT.md)
finished 6/6 fixed points with 12 charged calls and no refitting or later
receiver observations. A small cost ridge separates the 2010 pair on the
straight line; the 2015 pair has a near-flat straight-line connection.
Neither establishes global optima or changes the original failed fit labels.

The [long-recording covariance software check](prediction-observed-development/STRUCTURED_RECEIVER_LIKELIHOOD_RESULT.md)
matches a dense calculation on small examples and processes 64,080 generated
receiver reports with 26 calibration directions in 23.49 seconds and 353 MiB
peak memory through the existing shared state-space core. No observed long-flight fit or aircraft error-law claim follows
from this timing result. Six exact-law translation checks and a 120-epoch
saved training-prefix comparison now agree with dense whitening at the
actual coordinate scale. A [separately frozen native check](prediction-observed-development/STRUCTURED_RECEIVER_NATIVE_RESULT.md)
then agrees across all 26 physical calibration derivatives at one fixed
point. The [matched short-prefix fits](prediction-observed-development/STRUCTURED_RECEIVER_FIT_RESULT.md)
both passed their original stopping checks after 61 evaluations and agreed
on cost and fitted path. This checks computation under the same assumed law,
not aircraft error-law adequacy.

The [matched ESA 400/120 development comparison](prediction-observed-development/ESA_400_120_MODEL_MATRIX_INTERPRETATION.md)
closed all 24 frozen fits, with 20 passing numerical checks and four
zero-removal flat-disc fits not converging. Both complete settings, which
profile upstream removal, favor the specified-field globe on withheld
positions; its selected fit passes the stated physical screen. The other two
settings abstain. This is one already opened development flight, not an
independent detection. The [runtime record](prediction-observed-development/ESA_400_120_MODEL_MATRIX_RUNTIME.md)
and [portable evidence](prediction-observed-development/esa-400-120-matrix/runtime/portable-evidence.zip)
preserve all results and failures.
The [saved stopping audit](prediction-observed-development/ESA_400_120_MODEL_MATRIX_STOPPING.md)
finds that all four failed full corrections increased actual cost despite
predicting a small decrease. It used no new fits and did not change the
unresolved labels.

The [same-law ESA coverage check](prediction-observed-development/CROSS_POINT_COVERAGE_RESULT.md)
finds only 23/400 and 25/400 later heights inside nominal 95% ranges at two
saved calibration settings. A [height-error follow-up](prediction-observed-development/CROSS_POINT_HEIGHT_ANATOMY.md)
shows 375–377 consecutive misses and nearly identical error histories. Both
are saved-data diagnostics on one flight, not calibrated detection claims.

The [longer-flight candidate inventory](ilvis0-distance-inventory/RESULT.md)
completed all 232 strict file scans. Its fixed 10-minute/50-km rule found
five stretches on four dates, all already represented in the original
53-stretch study. It added no date group for later uncertainty work. It made
no Earth-model fits and left the original study unchanged. Its
[portable evidence](ilvis0-distance-inventory/runtime/portable-evidence.zip)
contains the frozen code, inputs, results and charges in a verified 0.78 MB
bundle. A [saved rejection audit](ilvis0-distance-inventory/REJECTION_AUDIT.md)
shows which screening flags were frequent without treating overlapping flags
as unique causes.

The separate [receiver/raw candidate scan](ilvis0-receiver-raw-inventory/RESULT.md)
closed 232/232 file tasks with no parse errors. It found 29 trajectories
totaling 314.6 minutes on 26 recorded dates, including 16 dates absent from
the original selected stretches. It removed fused-motion screening for
candidate discovery, so these are **not certified level flights**. The
[file and candidate ledgers](ilvis0-receiver-raw-inventory/RESULT.md) and
[verified portable evidence](ilvis0-receiver-raw-inventory/runtime/portable-evidence.zip)
retain the selection, source hashes, results and charges. No Earth-model fit
was made and the reserved ESA groups remain closed.
The follow-up [receiver-motion profile](ilvis0-receiver-motion-profile/RESULT.md)
reparsed those 29 sources using only timed receiver positions. All 29 tasks
passed. At the earlier study's reference values, nine profiles show elevated
climb and 14 show elevated course change. Twelve are below both references,
including six recorded dates absent from the original selected cohort. This
does not certify level flight or instrument attitude. The
[per-candidate table](ilvis0-receiver-motion-profile/motion.csv) and
[verified evidence](ilvis0-receiver-motion-profile/runtime/portable-evidence.zip)
preserve the descriptive result; no model fits were made.
The [alignment-only ablation](ilvis0-alignment-ablation/COMPARISON.md)
then rescanned those 29 candidate sources under every strict motion and
completeness rule except the fused alignment-status veto. All 29 file tasks
passed and it recovered the exact same five long intervals as the strict
232-file inventory. The [verified evidence](ilvis0-alignment-ablation/runtime/portable-evidence.zip)
preserves the sources, policy, results and charges. No candidate was promoted
or fitted.
The [conditional geometry profile](ilvis0-receiver-geometry-profile/INTERPRETATION.md)
then checked all 29 receiver/raw paths under the existing three-pair nuisance
projection. All 29 tasks passed. The widest unbounded local tangent leaves
median contrast fractions around 10⁻⁹ for every pair, so route geometry alone
does not qualify these tracks. It uses no observed gyro residual or model fit;
aircraft rotation is assumed independently removable. The
[verified evidence](ilvis0-receiver-geometry-profile/runtime/portable-evidence.zip)
retains all 261 pair/treatment scores and source bindings.

The [ESA known-motion control](prediction-observed-development/MOTION_ERROR_CONTROL.md)
now provides synthetic motion and separately known gyro, accelerometer and
receiver errors. It passes three software checks and is the next input for
testing an error-law method. It has not qualified the aircraft error law or
prediction coverage.
Its [matched contrast comparison](prediction-observed-development/MOTION_ERROR_CONTROL.md)
passes two additional checks and shows why short-span gyro changes alone
cannot establish sensor noise: a physical vibration can dominate or disappear
depending on the span.
The [saved generated whole-forecast audit](prediction-observed-development/GENERATED_SIMULTANEOUS_BOUND_RESULT.md)
then applies a 900-coordinate union allowance to the two completed
bound-aware paths. Both generated truths remain covered, but both fitted
point paths still fail the physical accuracy screen. This conditional
calculation makes no new fit or aircraft coverage claim.
The [saved calibration-direction audit](prediction-observed-development/GENERATED_WEAK_DIRECTION_RESULT.md)
finds a shared weak local combination of gyro gain, gravity adjustment and
vertical accelerometer bias in those two fits. It isolates a useful nonlinear
stress target without changing any result or identifying the cause of the
path miss.
The [saved interval-width decomposition](prediction-observed-development/GENERATED_BOUND_COMPONENTS_RESULT.md)
finds that calibration uncertainty contributes 71–81% of the median marginal
half-width in the two generated forecasts under their assumed error laws.
This is a verified arithmetic audit with no new fits or aircraft reads;
observed-aircraft coverage and physical point accuracy remain open.
The [eight-case saved noise-floor audit](prediction-observed-development/GENERATED_NOISE_FLOOR_AUDIT_RESULT.md)
finds a 17.39 m fixed-calibration conditional horizontal error scale under
the cohort's declared noise, versus its inherited 0.1 m clean-data screen.
All eight frozen failure labels are unchanged. This identifies a criterion
problem, while the aircraft error law and fitted calibration remain open.
A [six-case envelope software control](prediction-observed-development/FORECAST_ENVELOPE_CONTROL.md)
then checks that matched whole-path ranges can yield a descriptive unique
candidate and that broad overlapping ranges force abstention. It makes no
aircraft or Earth-model decision.
The [dual-target generated pilot](prediction-observed-development/DUAL_TARGET_GENERATED_RESULT.md)
passed its short wiring preflight and closed 2/2 full technical tasks with
2/2 converged fits. Separate physical and receiver ranges were saved before
later data. All 900 later receiver coordinates per case lie inside broad
roughly 208 m mean full horizontal ranges; the raw physical paths still fail
the old clean-data accuracy screen. This is a software result, not calibrated
aircraft coverage or model discrimination.
The [matched three-candidate generated preflight](prediction-observed-development/MATCHED_CANDIDATE_PREFLIGHT_RESULT.md)
passed its wiring gate. The [full 12-recording comparison](prediction-observed-development/MATCHED_CANDIDATE_GENERATED_RESULT.md)
then completed all 36 fits. Every later receiver path lies inside all three
candidate ranges, so every comparison abstains. This establishes a range-width
limit under the declared generated assumptions, not observed-aircraft coverage.
The [saved ESA weak-direction check](prediction-observed-development/ESA_SAVED_WEAK_DIRECTION_RESULT.md)
finds Z-axis gyro bias dominant in the weakest training direction of all 20
converged fits from the opened development flight. Four nonconverged fits
remain in its denominator; no reserved flight was opened.
The [saved training-duration check](prediction-observed-development/ESA_TRAINING_DURATION_WEAKNESS_RESULT.md)
compares 400 and 600 exact-prefix receiver reports from that same flight.
Extra earlier data strengthen the weak local calibration direction, but the
600-report fit still fails to cover later heights. It makes no new fit or
independent replication claim.
The [four-case generated motion control](prediction-observed-development/GEOMETRY_CALIBRATION_CONTROL_RESULT.md)
then crossed straight/turning paths with level/shallow-climb profiles under
identical generated IMU noise. All four technical tasks completed. The two
straight fits converged; the two turning fits stopped without convergence.
Saved turning tangents suggest more calibration sensitivity, but the failed
fits cannot qualify that comparison or an aircraft uncertainty rule.
The [turning-point replay](prediction-observed-development/TURNING_FIXED_POINT_RESULT.md)
reproduces both saved costs exactly. Every tested fraction of the bounded
correction raises actual cost although the full local linear correction
predicts a small decrease. The original fit failures remain unchanged.
The [known-optimum turning control](prediction-observed-development/TURNING_KNOWN_OPTIMUM_RESULT.md)
then converged in all four cases under two starts per route. This qualifies
the solver on constructed exact targets, while leaving the original noisy
turning fits and aircraft error law unresolved.
The [independent noisy-objective comparison](prediction-observed-development/TURNING_NOISY_SOLVER_RESULT.md)
tried two other bounded methods at both failed turning points. All four
searches stopped successfully under their own criteria, but reached virtually
the same costs and still failed the project's original stopping check.
The [separate one-sided numerical control](prediction-observed-development/ONE_SIDED_TURNING_RESULT.md)
passes both generated turning fits at exactly their old costs under a new,
tested local rule. The frozen original failure labels do not change. This
does not yet qualify a full three-model or aircraft comparison.
The [matched geometry follow-up](prediction-observed-development/MATCHED_ONE_SIDED_GEOMETRY_RESULT.md)
completed all six candidate fits on straight and turning generated routes.
Every fit passed both stopping checks, but all three saved prediction ranges
covered the later receiver path on both routes. Both model comparisons
abstain; the aircraft error law remains unqualified.
The [full ESA receiver-only audit](prediction-observed-development/FULL_RECEIVER_CONSISTENCY_RESULT.md)
checks all 64,080 reports in the opened development recording across eight
fixed time windows. Reported position precision and internal
position/velocity consistency vary modestly, but neither supplies an
independent position truth or qualifies aircraft prediction coverage.
The [speed-selected ground control](prediction-observed-development/GROUND_RECEIVER_CONTROL_RESULT.md)
finds 65 minutes of low-speed PPP reports with centimetre-scale relative
position scatter. It constrains short-term receiver behavior in that interval,
while leaving airborne and absolute accuracy unresolved.
The [overlapping raw-iMAR control](prediction-observed-development/GROUND_IMU_RATE_RESULT.md)
finds a 16.37°/h mean angular-rate-vector magnitude over 45 minutes of
low-speed ground time. Minute-scale variation and an end-of-interval yaw
event prevent assigning that mean to a background field or its cause.
The [second receiver-selected ground interval](prediction-observed-development/SECOND_GROUND_INTERVAL_RESULT.md)
provides another 30.7 minutes, about five hours later and at nearly the same
latitude. Its [raw iMAR baseline](prediction-observed-development/SECOND_GROUND_IMU_RESULT.md)
contains 553,345 samples with a 13.27°/h mean-vector magnitude, 3.10°/h
below the first stop. The sensor-axis vectors differ by 11.82°/h; visible
within-stop motion and unknown heading prevent identifying a geographic field.
The [1/10/60-second rate audit](prediction-observed-development/GROUND_RATE_SCALE_RESULT.md)
replays both stops, reproduces the saved minute bins and finds much larger
short-time variation than minute variation. It is logged IMU and airframe
motion together, not a calibrated sensor-noise law.
The [ground tilt check](prediction-observed-development/ESA_GROUND_TILT_CLOSURE_RESULT.md)
finds that the gyro predicts changes in accelerometer direction at both
stops, with much stronger agreement at the first. Yaw and sensor-only
variation remain unresolved.
The [full opened-flight parallel receiver check](prediction-observed-development/FULL_PARALLEL_GNSS_V2_RESULT.md)
matches two other PPP exports to `air1` across eight fixed windows. Most
relative differences are centimetres. In the last window `mosaic03`
differs by 0.28/0.23/0.34 m RMS north/east/up, while `pwrpak7` remains much
closer. A [speed-only split](prediction-observed-development/PARALLEL_GNSS_MOTION_PHASE_RESULT.md)
finds that the difference grows from fast flight through transition to the
final low-speed period. Shared antenna and processing prevent an
absolute-accuracy claim.
The [120-second fast-flight audit](prediction-observed-development/PARALLEL_GNSS_120S_RESULT.md)
then checks the same opened PPP sources on the withheld-forecast timescale.
Across 195 speed-selected windows, 95th-percentile end-to-start differences
are about 1–2.5 cm per axis, while persistent offsets are larger. It cannot
see errors shared by the three exports or calibrate an aircraft error law.
The [reported-precision comparison](prediction-observed-development/PARALLEL_GNSS_REPORTED_PRECISION_RESULT.md)
uses the same 195 windows and 23,399 paired positions per alternate export.
For `mosaic03`, 5.9% of north differences exceed three times the summed
reported precision scale. Shared antenna means these are descriptive
ratios, not statistical significance scores or absolute error bounds.
The [saved fast-window decomposition](prediction-observed-development/PARALLEL_GNSS_WINDOW_DECOMPOSITION_RESULT.md)
passes two known-answer tests and all 195 window identity checks. Persistent
within-window means explain 90–99% of the relative mean-square receiver
disagreement across axes and exports. It reads no originals or protected
groups and cannot measure common receiver error.
The [alternate-PPP forecast rescore](prediction-observed-development/ESA_ALTERNATE_PPP_SCORING_RESULT.md)
then holds the original fits and 120 withheld epochs fixed while changing
only which PPP export supplies later positions. Both complete ESA settings
keep the same globe/flat and specified/zero-field numerical ordering, with
metre-scale versus kilometre-scale candidate differences. This is one opened
flight with shared-antenna exports, not independent validation.
The [fixed-forecast receiver-shift bound](prediction-observed-development/ESA_FIXED_FORECAST_RECEIVER_MARGIN_RESULT.md)
reproduces all six saved model scores and uses three exact known-answer
checks. About 1.3 km per later report would tie the two globe scores, or
2.0 km the globe/disc scores, with their forecasts and coordinate metric
held fixed. It is a saved-only sensitivity diagnostic, not a receiver
accuracy estimate or scientific decision.
The [alternate PPP training material](prediction-observed-development/ESA_ALTERNATE_TRAINING_MATERIAL_RESULT.md)
matches the same 400 earlier ESA reports and changes only their coordinate
fields. The two compressed inputs are 68 KB together; their north/east/up
RMS differences from `air1` are 1.24/1.58/2.76 cm and 0.72/0.69/3.49 cm.
No later positions were staged by the preparation. A separate finite refit
comparison passed ten source-bound qualification tests and [closed all six
bounded tasks](prediction-observed-development/ESA_ALTERNATE_TRAINING_REFIT_RESULT.md)
in 19.6 minutes, with six numerical passes and no errors. Both alternate
training sources retain the same numerical model ordering on the same
120 later `air1` reports. This is one development flight, not independent
validation or calibrated uncertainty.
The first strict parse failure and the separately validated printed-counter
rollover are preserved.
The [whole-path compatibility control](prediction-observed-development/JOINT_FUTURE_PROFILE_RESULT.md)
passes five synthetic algebra checks. Its [sealed generated replay and
saved-data audit](prediction-observed-development/GENERATED_JOINT_PROFILE_SAVED_RESULT.md)
find full-range corrections that invalidate the local tangent: native paths
differ by metres to tens of metres. Both replay task gates remain terminal
failures; the saved audit explains the second task's exact accounting gap.
No aircraft fit or scientific decision uses these linear costs.
The [separate radius-0.1 generated task](prediction-observed-development/GENERATED_LOCAL_PROFILE_RESULT.md)
passes its complete replay and receipt checks with no new model fits. Its
smaller calibration steps still leave up to about 1.3 m RMS native-versus-
tangent discrepancy on an axis; it does not qualify a model decision.
The [joint whitening adapter](prediction-observed-development/CONDITIONAL_JOINT_PROFILE_RESULT.md)
passes an independent dense conditional-covariance control and preserves
training-to-future nuisance dependence. A reliable local or nonlinear
profile and observed qualification remain open.
The [known-calibration audit](prediction-observed-development/GENERATED_CALIBRATION_RECOVERY_RESULT.md)
compares fourteen fitted sensor parameters with their generated truths. RMS
differences are 0.47 and 0.35 allowed half-ranges, and three parameters
reach bounds despite interior truth. It reads only sealed generated artifacts
and does not identify a cause of the inaccurate physical paths.
The [fixed-parameter substitution](prediction-observed-development/GENERATED_CALIBRATION_SUBSTITUTION_RESULT.md)
closes both native generated cases, reproduces the saved paths, then replaces
fitted calibration blocks with their known generating values without
refitting other parameters. Every replacement worsens the later physical
path, demonstrating strong nuisance coupling in these cases. It does not
calibrate the aircraft error law or identify the path-miss cause.
The [eight-case generated cohort](prediction-observed-development/GENERATED_BOUNDED_COHORT_RESULT.md)
closes 8/8 technical tasks, all numerically converged. None passes its coded
physical path screen; all eight known futures lie inside broad assumed
marginal coordinate intervals. The cases use one route with fresh noise
seeds, so they do not qualify aircraft coverage or independent geometry.
The [finite nonlinear follow-up](prediction-observed-development/GENERATED_WEAK_DIRECTION_NONLINEAR_RESULT.md)
then closes 2/2 generated tasks and eight charged native forecasts. A fixed
small move along that direction changes the later path by less than 0.7 m;
its tangent error is about 0.013 m. The original 91–109 m path misses remain.
The earlier failed preflight is preserved separately.

The [twelve-pair saved gyro comparison](ilvis0-pair-rate-scale/RESULT.md)
reproduces the published one-second differences from verified caches and
shows smaller between-recorder differences after one-minute averaging.
An [earlier-only relative-alignment check](ilvis0-pair-alignment/RESULT.md)
improves later-half agreement in 11 pairs, but substantial differences remain.
Neither check identifies intrinsic sensor error or twelve independent flights.

The [ESA 400/120 receiver-only control](prediction-observed-development/ROLLING_ORIGIN_400_RECEIVER_CONTROL.md)
uses the same already opened development window as the sealed IMU forecast.
Two fixed GPS-only rules miss by 417–424 m horizontally, versus 0.56 m for
the conditioned IMU forecast. A [later reported-velocity control](prediction-observed-development/ROLLING_ORIGIN_400_VELOCITY_CONTROL.md)
misses by 418 m. These fixed-course controls do not isolate the gyro channel
or establish independent accuracy.
An [earlier-only GNSS velocity check](prediction-observed-development/GNSS_VELOCITY_CONSISTENCY.md)
finds position-derivative versus reported-velocity RMS differences of
0.016/0.007/0.036 m/s across north/east/up. This confirms internal
consistency on 398 training epochs; the two outputs share one PPP solution.
A separate [5 Hz receiver motion check](prediction-observed-development/GNSS_5HZ_MOTION_RESULT.md)
compares fixed course-change spans with the logged body-down gyro rate on
the same opened flight. Both prepaid, zero-fit tasks pass: 397/400 two-second
and 389/400 ten-second centers have support, with correlations 0.915 and
0.969. Aircraft course is not body heading, so these are descriptive motion
checks rather than gyro-noise or prediction-coverage estimates. The
[sealed runtime record](prediction-observed-development/gnss-5hz-motion-runtime/README.md)
and [portable evidence](prediction-observed-development/gnss-5hz-motion-runtime/portable-evidence.zip)
retain the complete study.
An independent [known-motion check and 5 Hz aliasing control](prediction-observed-development/OBSERVED_ERROR_PLAN.md)
confirm the comparison's sign and show that identical sampled IMU, receiver
position and velocity can still have different underlying motion. These are
software controls, not extra aircraft fits or an error bound.
The [200/120 earlier-origin check](prediction-observed-development/ROLLING_ORIGIN_200_INTERPRETATION.md)
then fixed a second training/withheld cut inside the same opened ESA flight.
Its preflight verified 95,868 IMU packets and excluded all 120 scoring
positions from the fit. Both fits and both conditioning tasks sealed and
passed. The conditioned forecast misses by 0.467 m horizontally and 0.240 m
in height; adjacent errors remain correlated. This is same-flight development
evidence, not independent prediction-error coverage.
Its [fit runtime record](prediction-observed-development/rolling-origin-200-fit-runtime/README.md)
and [portable fit evidence](prediction-observed-development/rolling-origin-200-fit-runtime/portable-evidence.zip)
preserve the sealed optimization. The separate
[conditioning runtime record](prediction-observed-development/rolling-origin-200-conditioning-runtime/README.md)
and [portable conditioning evidence](prediction-observed-development/rolling-origin-200-conditioning-runtime/portable-evidence.zip)
preserve the fixed-fit correction without another fit.
The [conditional error-bound calculation](prediction-observed-development/PREDICTION_ERROR_ENVELOPE.md)
passes six generated checks. Those checks verify how supplied physical
limits propagate; they do not establish the limits for this aircraft or
qualify coverage on another flight.
The [changing-drift candidate](prediction-observed-development/INTEGRATED_DRIFT_LAW_PLAN.md)
matches an independent dense covariance and conditional-forecast calculation.
A separate generated-IMU integrator checks the local measurement path. Its
[frozen eight-case pilot](prediction-observed-development/integrated-drift-pilot/RESULT.md)
closed all technical tasks. Only 3/8 generated histories kept every later
coordinate within nominal marginal ranges; 6/8 stayed inside a conservative
simultaneous range. Eight cases cannot establish coverage. The law remains
unqualified. The
[runtime record](prediction-observed-development/integrated-drift-pilot/RUNTIME.md)
and [portable evidence](prediction-observed-development/integrated-drift-pilot/runtime/portable-evidence.zip)
preserve the original forecasts and scores.
The [independent-group count check](PREDICTION_GROUP_COUNT.md) shows why the
seven reserved ESA groups can test transfer but cannot by themselves certify
95% flight-level prediction coverage with 95% confidence.
The [flight-group decision control](FLIGHT_GROUP_DECISION.md) keeps
incomplete groups in the count and checks shape before the background
field. It needs independently calibrated tests within each group.
The [reference-sample audit](prediction-observed-development/GROUP_RANK_RESOLUTION_RESULT.md)
checks the exact rank calculation and finds one saved reference draw per
model, route and noise-law combination. That is too few to supply the
flight-group tests.
The [reference-draw work bound](FLIGHT_GROUP_DECISION.md#when-additional-reference-draws-cannot-change-a-rejection)
verifies when a future rejection decision is settled even with unfinished
draws. It uses the original draw count and counts unused draws against
rejection.
The [ESA saved-table check](prediction-observed-development/ESA_RINEX_CODE_COMPARISON_RESULT.md#reproduce-the-comparison)
verifies the forecast rankings and recomputes the receiver differences from
three report files alone.
The separate [changing-gyro-bias pilot](prediction-observed-development/integrated-drift-v2-pilot/RESULT.md)
closed all 16 fresh-seed generated tasks. All 16 whole histories stayed
inside its predeclared conservative simultaneous range; 10/16 stayed inside
every nominal marginal range. Its [runtime record](prediction-observed-development/integrated-drift-v2-pilot/RUNTIME.md)
and [portable evidence](prediction-observed-development/integrated-drift-v2-pilot/runtime/portable-evidence.zip)
preserve the sealed forecasts and scores. This is a development result, not
an observed-aircraft coverage claim.
The [independent 256-history generated check](prediction-observed-development/integrated-drift-v2-validation/RESULT.md)
then completed all tasks but **failed** its frozen coverage gate: zero
whole-history exceedances in 128 no-vibration cases, four in 128 vibration
cases, against a limit of one each. Its final simultaneous half-width was
25.59 m per coordinate. The [runtime record](prediction-observed-development/integrated-drift-v2-validation/RUNTIME.md)
and [portable evidence](prediction-observed-development/integrated-drift-v2-validation/runtime/portable-evidence.zip)
retain all cases, including failures. No observed-aircraft range follows.
The [saved failure diagnosis](prediction-observed-development/integrated-drift-v2-validation/VIBRATION_DIAGNOSTIC.md)
locates three maxima at the first withheld second and one at second 69;
their absolute errors are 0.15–0.67 m. The strata's median maximum scores
are similar, and the exploratory four-versus-zero association does not
establish a vibration cause. A separate [clean 100 Hz control](prediction-observed-development/integrated-drift-v2-validation/CLEAN_PROPAGATION.md)
limits integration error below 0.0004 m in both motion modes.
At the first withheld second, standardized error RMS is near one on each
axis in both strata, so the failures do not show a broad early variance
deficit. Four tail events still prevent the frozen gate from certifying
coverage; a true failure rate below 5% remains compatible with these data.
The [16-pair matched-noise control](prediction-observed-development/paired-vibration-control/RESULT.md)
then found no failures in either motion setting. Switching the generator's
10 Hz vibration changed the maximum standardized score by at most 0.000224
within a pair. At each one-second receiver report, that vibration repeats
the same 0.2 mm north offset and zero pitch perturbation. Thus the earlier
four-versus-zero split is not explained by this vibration control;
the frozen 256-case gate remains failed. That result motivated a motion
control visible at receiver times.
The separate [receiver-visible 0.37 Hz motion pilot](prediction-observed-development/nonaliased-motion-control/PILOT_RESULT.md)
closed 16/16 matched-noise pairs. It changes receiver-time north position
by 0.2 m, yet the largest paired change in maximum standardized error is
0.0016; neither arm missed its range. This is a small software control,
not a coverage qualification. The failed 256-history gate remains intact.
The [range-usefulness note](prediction-observed-development/INTERVAL_USEFULNESS.md)
shows that two single-coordinate endpoint ranges with 25.59 m half-widths
would need centers more than 51.18 m apart to be disjoint; matched
three-model forecasts under this law have not been sealed.
The note also compares three archived forecasts on the one complete ESA
development setting: their withheld model centers differ by 0.67–1.42 km
after 60 seconds. This is descriptive model separation, not a calibrated
decision. A separate [fresh 256-history threshold check](prediction-observed-development/threshold-42-validation/RESULT.md)
tested a 4.2 standardized threshold chosen after the first gate failed.
It completed all 256 technical tasks and passed its frozen generated gate:
1/128 range failures without the generator's vibration, 0/128 with it,
and a 29.57 m median endpoint half-width. The earlier gate remains failed.
The [execution record](prediction-observed-development/threshold-42-validation/RUNTIME.md)
and archived study preserve the source, charges, forecasts and scores.
Neither range is yet calibrated for real aircraft.
A [training-only receiver covariance audit](prediction-observed-development/GNSS_COVARIANCE_AUDIT.md)
matches all 400 earlier reports to the original export. All printed position
and velocity matrices pass an algebraic check; the shared PPP processing and
missing cross-time covariance still prevent an accuracy claim.
A [parallel receiver check](prediction-observed-development/PARALLEL_GNSS_RESULT.md)
matches two more PPP exports at all 400 earlier times. Position differences
are centimetres, but the common antenna and possible shared processing prevent
an absolute accuracy claim.
A [common-time follow-up](prediction-observed-development/PARALLEL_GNSS_TIME_RESULT.md)
uses reported velocity to account for the submillisecond time offsets. East
differences fall from 2.2 to 1.6 cm and 2.1 to 0.7 cm RMS; this remains
exploratory relative agreement. Lag-one correlations of the adjusted
differences are 0.70–0.86, so they are not independent white noise.
A [three-receiver training-fit check](prediction-observed-development/PARALLEL_GNSS_FIT_RESULT.md)
reuses both sealed fitted trajectories without refitting. All six comparisons
have about 0.8 m north and 1.0 m east RMS training error, much larger than
between-receiver differences. These are raw in-sample fits, not conditioned
future predictions or a calibrated error law.
The [conditioned forecast cross-check](prediction-observed-development/PARALLEL_GNSS_FORECAST_RESULT.md)
reproduces the sealed `air1` score, then scores the unchanged 120-epoch forecast
against both other PPP streams: horizontal RMS 0.554–0.563 m and height RMS
0.169–0.197 m across all three receivers. This same-flight development result
does not establish independent accuracy or coverage.
A [GPS-only constant-turn follow-up](prediction-observed-development/ROLLING_ORIGIN_400_TURN_CONTROL.md)
uses the last 60 earlier velocity reports and misses the later 120 reports
by 448 m horizontally, versus 418 m for the fixed-course GPS-only rule.
The rule was designed after the earlier outcome and is development evidence.

[Saved ESA forecast versus receiver precision](esa-prediction-error-scale/README.md):
22 completed forecasts are matched to the same receiver epochs; two original
deadline failures remain listed. The receiver's centimetre precision does not
describe the full later prediction error. This is a descriptive check on one
development recording, with no new fit or confidence claim.
The [saved error-dependence check](esa-prediction-error-scale/CORRELATION.md)
uses those same 22 forecasts. Successive errors remain highly correlated even
after removing linear drift. For the specified-field globe, later RMS errors
are 84–178 times the fitted earlier residual RMS by axis. This describes one
development recording; it makes no new fit or independent-flight claim.
The [separate NASA pilot's saved scores](ilvis0-retrospective-prediction-pilot-v2/ERROR_STRUCTURE.md)
show later-to-earlier RMS ratios of 13–47 across the three axes for its nine
numerically qualified specified-field settings. Those settings come from three
development recordings and do not calibrate a forecast error law.
Their saved one-second errors rise through four withheld quarters. The
[completed earlier-only transfer check](prediction-rolling-origin/INTERPRETATION.md)
uses the same three development recordings. It returns all 48 starts, with 34
numerical passes and 14 nonpasses; eight of twelve repeated settings match at
both cuts. The north later/earlier RMS ratio ranges from 0.44× to 4.09×, so
these recordings do not calibrate one future-error multiplier. The
[frozen plan](prediction-rolling-origin/PLAN.md),
[recovery procedure](prediction-rolling-origin/RECOVERY.md) and six-check
source-bound publication receipt preserve its method and accounting. Starts
were selected by earlier training cost, never by later error.
Four [new retrospective development groups](prediction-group-transfer/README.md)
have been selected using only route, IMU type and provenance metadata. Their
selection itself produced no model result.
Their [transfer plan](prediction-group-transfer/OBSERVED_PLAN.md) now fixes an
earlier-only empirical error reference and a sixteen-start diagnostic grid.
The three-check reference builder ignores later scores. After 24 source-bound
and five recovery checks, the study sealed all 16 starts; six passed their
numerical checks. The [verified saved-only report](prediction-group-transfer/RESULT.md)
scores three of four groups at the second cut: all three meet the fixed
descriptive error reference and physical prediction screen. One abstains.
This is not calibrated coverage.
The [saved stopping diagnostic](prediction-group-transfer/STOPPING_DIAGNOSTIC.md)
preserves all ten numerical failures and identifies which fixed check each
missed; it does not promote a failed fit.
A later [metadata-only inventory](prediction-group-transfer/EXPANSION_INVENTORY.md)
identifies one preselected representative in each of the 20 conservative
groups unused by those seven development recordings. All 20 are IMU21; 18
are southern. No original recording, gyro value, model outcome or protected
ESA group was read, and no fit was run. The inventory does not authorize a
larger observed study without a separately frozen error law and allowance.
The [receiver-only forecast control](receiver-only-forecast-baseline/INTERPRETATION.md)
reuses the three sealed pilot receiver splits. A last-minute constant-velocity
forecast has 87–351 m later horizontal RMS. A separately frozen
[spherical-path control](receiver-only-geodesic-control/INTERPRETATION.md)
improves that to 33–189 m on the identical withheld epochs. Both controls
complete all three tasks with zero native calls. The available IMU forecasts
remain closer on B and C, but these controls do not identify the gyro's
separate contribution or calibrate an Earth-model decision.

[Training-only receiver-error assessment](ilvis0-shared-training-error/README.md):
14 source-bound software checks pass for an exact-rational shared scale
calculation. All 18 [predeclared recorded training-prefix calculations](ilvis0-shared-training-error/recorded-assessment/README.md)
complete from 292 earlier receiver fixes on one development recording. The
declared error law and aircraft prediction coverage remain unverified.

[Aircraft prediction-error plan](PREDICTION_ERROR_LAW_PLAN.md): the simplified
400-history identification study is complete. Twelve short native controls
pass real training fits and distinguish future physical-position from
receiver-report covariance across three models, both processing cases and two
synthetic IMU error-input forms. The [source-bound 48-case clock and calibration
matrix](prediction-aircraft-error-integration/RESULT.md) passes every technical
check, but none of its short fits converge or pass the physical prediction
check. Empirical aircraft coverage remains open.
A separate training-only comparator now requires matched measured prefixes
before comparing candidate error-law scores. Its four local checks pass;
no law-selection or coverage claim follows from those checks.
The [paired generated-aircraft study](prediction-paired-law/RESULT.md) now
verifies 12 recordings and 24 matched fits. All pass numerical and physical
screens, but the training-score minimum identifies the generating IMU law in
only 6/12 recordings.
Their fixed-parameter forecast scales differ by at most a factor of 1.0000023.
The two laws were set to nearly the same accumulated noise at 300 Hz.
A longer same-cadence identification run is not warranted.
The [paired bound-family study](prediction-paired-bound-family/RESULT.md)
verifies 24/24 generated recordings and 48/48 matched fits after a separate
four-recording technical continuation. Both target interval unions contain
every withheld coordinate in this small development matrix. Eighteen focused
method checks and seven recovery checks pass. Statistical coverage and
observed-aircraft adequacy remain open.
The [first 96-recording whole-period attempt](prediction-simultaneous-law-family/RESULT.md)
closed with 96 sealed package-import errors and zero numerical calls. It gives
no coverage evidence. The [fresh 96-recording cohort](prediction-simultaneous-law-family-v2/RESULT.md)
closed with 92 complete paired forecasts and four sealed time-limit failures.
All later coordinates fell inside both target intervals on the 92 scored
recordings. Counting the four failures gives a 9.28% one-sided 95% upper
failure bound, so the frozen 5% gate failed. A qualified continuation completed
only 12 tasks that had never started; no sealed result was rerun.
The [runtime audit](prediction-simultaneous-law-family-v2/RUNTIME.md) records
about nine hours of combined work. A [new-cohort plan](prediction-simultaneous-law-family-v3/PLAN.md)
froze a separate 12-hour allowance and new seeds. Its source-bound tests,
recovery checks and separate frozen-worker preflight passed. The original
launch closed after four completed recordings and four interrupted starts; a
qualified continuation completed the other 92 tasks without repeating sealed
work. The [saved-result audit](prediction-simultaneous-law-family-v3/RESULT.md)
verified 96/96 tasks, 95/96 passing recordings, and both withheld targets in
all 95 scored recordings. One numerical failure counts against the frozen gate;
the exact one-sided 95% upper failure bound is 4.85%, below 5% for this
generated mixture. Observed-aircraft coverage remains untested.
A [saved fitted-error audit](prediction-simultaneous-law-family-v3/FITTED_INNOVATIONS_RESULT.md)
verified the same archived lineage and counted all 192 fits. Among the 190
passing fits, median height correlation one report apart was −0.043 under
either error law; the largest absolute value across 95 scorable recordings
was 0.286. The opened ESA development fit instead has correlation 0.825.
Different history lengths and error processes prevent a calibrated comparison;
the subsequent matched full-fit pilot failed its physical accuracy gate, so a
passing full-path control remains necessary.
A [local tangent-projection control](prediction-observed-development/LOCAL_PROJECTION_NULL_RESULT.md)
used the two sealed ESA 600-report fits and 2,048 white-error histories per
law. None reproduced the saved height correlations of 0.825 at one lag or
0.538 at twenty lags. This rules out the 26-direction **linear fit projection
alone**, under the declared fixed covariance, as an explanation; it does not
qualify the covariance or replace nonlinear full-fit controls.
The [complete-fit generated pilot](prediction-observed-development/FULL_FIT_INNOVATION_NULL_RESULT.md)
passed 14 source-bound wiring tests, five recovery tests and a frozen-worker
preflight, then closed both 600-report tasks. Both fits converged with rank
26 and near-zero fitted height correlation. **The study gate failed:**
training horizontal error versus known truth was 55.3 and 33.3 m, above the
[coded physical screen](prediction-observed-development/GENERATED_ACCURACY_RULE_ERRATUM.md);
later error was 219.2 and 156.1 m. Its terminal
outcome remains unchanged. Fitted innovation behavior alone does not qualify
a physical prediction range.
A [saved generated-path audit](prediction-observed-development/GENERATED_PATH_ERROR_AUDIT_RESULT.md)
finds that the training receiver positions are only 0.37–0.38 m horizontal
RMS from known truth, while the fitted paths are 33–55 m away and grow to
75–120 m RMS in the last training minute. The large pilot miss is thus in
the fitted physical paths, not generated receiver noise. It does not isolate
the calibration or motion cause.
The [first bound-aware technical preflight](prediction-observed-development/BOUND_AWARE_GENERATED_PILOT_V1_RESULT.md)
preserved a 0/1 failure when its native-call reserve ended before the extra
operator pass. A separately frozen [revised pilot](prediction-observed-development/BOUND_AWARE_GENERATED_PILOT_V2_RESULT.md)
passed its new nine-query preflight and both fresh full technical tasks.
Both fits converged and all 300 later generated epochs lie inside their
affine intervals, but the original point paths fail the [coded physical
screen](prediction-observed-development/GENERATED_ACCURACY_RULE_ERRATUM.md)
at 108.60 and 91.31 m. Two cases do not qualify nonlinear or aircraft
prediction coverage.
A [saved training-error morphology audit](prediction-observed-development/INNOVATION_MORPHOLOGY_RESULT.md)
measured all 120 lags and cross-axis relationships in the two opened ESA
training fits. Height retains correlation 0.825 at one report and 0.538 at
twenty; 71.2% of its mean-removed power lies at periods over 60 reports.
A single positive exponential captures the first twenty lags approximately
but misses the negative correlation near lag eighty. This is a descriptive
stress target, not an identified physical error source.
A [saved receiver-quality cross-check](prediction-observed-development/TRAINING_QUALITY_AUDIT_RESULT.md)
finds strong ordinary association between raw fitted height difference and
PDOP/satellite count, but those associations reverse after report-to-report
or cubic-time adjustments. The whitened height residual's time-adjusted PDOP
correlation is +0.005. Receiver quality is therefore not a demonstrated
source of the persistent height error.
The development adapter passes a short native two-law control and binds the
saved ESA recording-187 split without opening later receiver rows. The
[full-size preflight](prediction-observed-law-preflight/RESULT.md) then passed
all four no-fit tasks on 360,028 IMU packets and 1,200 receiver epochs. Each
task used 601,895 native calls and about 27.5 minutes in a four-worker run;
operator storage was 6.7–10.0 MiB. This qualifies construction and the
withheld-data boundary, not real-aircraft error coverage. The first frozen
attempt stopped before native work on an input-key mismatch; its failure is
retained separately from the passing corrected run.
The [finite observed development pilot](prediction-observed-development/DIAGNOSIS.md)
sealed a technical failure after charging its 3,000,000 native-call allowance.
Both law-specific fits converged in nine evaluations and both forecasts were
saved, but the second receiver-measurement bound was unfinished. The withheld
receiver positions were not opened, so there is no observed coverage result.
The saved partial work supported a separately frozen continuation without
refitting either law. A [generated native check](prediction-observed-development/CONTINUATION_PLAN.md)
reproduced the sealed receiver bound, diagnostic, both law unions and withheld
score exactly with zero refits. The separate frozen worker smoke passed 1/1
generated task, and seven finite interruption checks qualified task recovery.
The [recording-187 continuation](prediction-observed-development/CONTINUATION_RESULT.md)
then completed 1/1 task and scored 400 later receiver positions. Both
forecasts fail the preset horizontal accuracy limits, at about 249 m RMS
later error. Interval coverage under assumed laws is uncalibrated and the
scientific result remains abstain. The original failure is unchanged; seven
independent confirmation groups remain protected.
The [saved error-trend audit](prediction-observed-development/DRIFT_AUDIT.md)
finds a 41.6 m/min east-error trend over the withheld period for both laws.
It makes no fit, correction or causal claim.
The [fixed receiver-only reference](prediction-observed-development/RECEIVER_REFERENCE_RESULT.md)
scores the same later positions: local straight-velocity and spherical
constant-course rules miss by 535 and 572 m horizontal RMS, versus about
249 m for the saved IMU forecast. This one-recording development comparison
does not establish absolute adequacy or isolate the gyroscope.
The [sealed generated-error comparison](prediction-observed-development/TRAINING_ADEQUACY_COMPARISON.md)
finds 2.25–3.19 m training horizontal RMS among 24 noisy known-answer cases,
versus about 40 m for the recorded ESA development fit. The synthetic noise
levels are assumptions, and none of the 24 generated later forecasts passes
the preset accuracy screen. This does not identify the recorded error's cause.
The [saved-rate sampling audit](prediction-observed-development/RATE_HYPOTHESIS_AUDIT.md)
reproduces the original 360,028 constructed increments exactly and measures
left/right integration differences without refitting. Signed final component
differences are small, but they do not bound navigation-position differences
or establish the iMAR instrument's actual sampling convention.
The [first fixed-point native rate comparison](prediction-observed-development/RATE_PROPAGATION_V1_RESULT.md)
sealed all three tasks but failed its exact baseline check: its ordinary tangent
kernel differs from the original extended-precision kernel by 0.0000145 m in
height at worst. The failed gate and three charges are preserved. The saved
alternative trajectories are not promoted into a scientific comparison.
The [new matching-kernel comparison](prediction-observed-development/RATE_PROPAGATION_V2_RESULT.md)
passed three technical tasks with the original fixed fit and no refits. Left and
right sample holds change later horizontal trajectories by 43.37 and 19.47 m
RMS relative to the original. All three retain large receiver errors; the
actual instrument sampling convention and scientific decision remain unresolved.
The first six-task generated refit control sealed as terminal because its gate
required convergence from deliberately short, nonconverged reference fits.
The separate [corrected control](prediction-observed-development/RATE_REFIT_V2_SMOKE_RESULT.md)
reproduces all six reference fits and forecasts and passes the technical gate.
The [observed development refits](prediction-observed-development/RATE_REFIT_V2_RESULT.md)
then pass all six numerical checks, but all three rate assignments under both
error laws fail the preset physical-accuracy screen. Training horizontal RMS
is 37.69–39.96 m and later RMS is 240.37–249.41 m. The right-hold method has
the smallest later error in this one recording, but later positions cannot
select the instrument convention. The scientific result remains abstain, and
the seven reserved ESA groups remain unopened.
The [saved-only shared-error diagnostic](prediction-observed-development/RATE_REFIT_COMMON_RESIDUAL.md)
then shows 245.85 m of later horizontal RMS common to all three rate methods,
compared with 5.87 m RMS method spread. It uses no new fit or protected group.
This narrows the explanation of the failed development forecasts without
identifying the physical cause or changing the abstention.
The [sealed historical comparison](prediction-observed-development/RATE_REFIT_HISTORICAL_COMPARISON.md)
checks the same interval, training rows, receiver policy and calibration bounds
against an earlier receiver-only weighted fit. That earlier fit missed later
positions by 7.80 m horizontal RMS, versus 249.41 m for the newer fit with a
declared IMU-error covariance. The comparison identifies a modeling difference
to isolate; it does not establish which weighting describes the instrument.
The [matched weighting control](prediction-observed-development/WEIGHTING_CONTROL_RESULT.md)
then fit the same development interval in current code with receiver-only
weighting. It reproduced every earlier fitted parameter and forecast coordinate
exactly and passed the preset held-out accuracy screen at 7.803 m horizontal
RMS. The current added-IMU-error fit remained at 249.411 m. Both completed
numerically; the discrepancy is the added, unmeasured error law in this
recording. The scientific decision remains abstain.
The [fixed-parameter cross-score](prediction-observed-development/ERROR_LAW_CROSS_SCORE_RESULT.md)
then completed its one source-bound development task with no refit or later
GPS read. It reproduced both original training costs. The added IMU-error
law scores its own saved fit at 13.24 and the receiver-only saved point at
145.88. This rules out a missed receiver-only *saved point* as the sole
explanation for the weighted result, while leaving the law's physical validity
and its earlier-data-conditioned forecast open. Seven confirmation groups
remain reserved.
The first [conditional-forecast attempt](prediction-observed-development/CONDITIONAL_FORECAST_V1_RESULT.md)
then stopped at its frozen 600,000-native-call ceiling while rebuilding the
full error operator; it produced no forecast score. The task and charges are
retained. A single-pass operator construction is the next technical check.
The [single-pass follow-up](prediction-observed-development/CONDITIONAL_FORECAST_V2_RESULT.md)
built the full operator in 361,228 native calls, then failed because it
compared unlike covariance hashes. Its failure is retained without a later
GPS score. A separately frozen replay of early cost and log-determinant
followed.
The [corrected single-pass check](prediction-observed-development/CONDITIONAL_FORECAST_RESULT.md)
then completed one source-bound task. Its early log-determinant and weighted
cost replayed exactly. On the same 400 later receiver reports, the
fixed-parameter conditional mean reduced horizontal RMS from 249.41 m for
the uncorrected trajectory to 2.85 m and passed the preset accuracy screen.
The [same-law cross-point check](prediction-observed-development/CROSS_POINT_CONDITIONAL_RESULT.md)
later applied that complete conditional error law to the receiver-only saved
fit, without refitting or using later GPS in the forecast. Its conditional
horizontal RMS was 9.07 m, versus 2.85 m at the weighted saved fit; both
passed the preset physical screen. Two preceding technical failures are
preserved. This one-flight development comparison does not qualify the
error law's uncertainty or an Earth-model decision.
The [matched coverage check](prediction-observed-development/CROSS_POINT_COVERAGE_RESULT.md)
then used the same sealed forecasts and later receiver reports. Only 23/400
and 25/400 heights fall inside their nominal 95% intervals. The height
uncertainty failure persists at both saved calibration settings. These are
correlated reports from one development flight, not independent coverage
trials; the cause and replacement error law remain open.
The [saved uncertainty diagnostic](prediction-observed-development/CONDITIONAL_COVERAGE_RESULT.md)
then found that only 25/400 later receiver heights lie within the declared
nominal 95% marginal intervals, while 400/400 north and east errors do.
The three-component nominal 95% region contains 37/400 reports. This one
strongly correlated segment cannot calibrate coverage; the current error law
does not support an uncertainty claim.
The first [local calibration-uncertainty task](prediction-observed-development/LINEAR_UNCERTAINTY_V1_RESULT.md)
stopped after a correct early covariance replay because the sealed forecast
does not retain its full Jacobian. The technical failure and complete charge
are preserved; a new task must generate and verify that derivative.
The [next bounded attempt](prediction-observed-development/LINEAR_UNCERTAINTY_V2_RESULT.md)
also ended before derivative generation because its adapter supplied the
wrong bounds-object type to the native forecast constructor. That technical
failure and its charge are preserved separately.
The [third, corrected local check](prediction-observed-development/LINEAR_UNCERTAINTY_V3_RESULT.md)
passed all 26 training derivative replays and found full local rank with an
in-bounds step. Adding local parameter uncertainty increased nominal height
coverage only from 25/400 to 26/400 later receiver reports; the observed
error law remains unqualified.
The assumed law is not calibrated for this instrument; seven confirmation
groups remain reserved and the scientific decision is abstain.
The [earlier-only 600/200 recheck](prediction-observed-development/TRAINING_SPLIT_RECHECK_PLAN.md)
has a verified sealed-input split and passing generated no-leak and recovery
checks. [Both preselected fits converged](prediction-observed-development/TRAINING_SPLIT_FIT_RESULT.md)
without using the 200 later receiver positions; both fixed-law conditioning
tasks also closed. The [saved-only score](prediction-observed-development/TRAINING_SPLIT_SCORE_RESULT.md)
finds about 1.94 m horizontal and 0.24 m height RMS after conditioning for
either law, with 200/200 heights inside nominal ranges. The older, later
800/400 forecast still misses most nominal height ranges. This is one
retrospective development recording, not independent coverage validation.
The [fixed horizon diagnosis](prediction-observed-development/HEIGHT_HORIZON_RESULT.md)
uses the sealed forecasts without a new fit: the longer forecast covers 25/100
heights in its first 100-second bin and none in the next three. Its correction
keeps growing while the raw height error changes sign; the physical cause is
unresolved.
The [fixed-fit 600/400 extension](prediction-observed-development/TRAINING_SPLIT_EXTENSION_RESULT.md)
then completed both prespecified laws without refitting or using later receiver
positions. Its first 200 conditional forecasts exactly replay the prior
600/200 result. Height coverage is 96/100 on reports 800–899 and 0/100 on
900–999. The older 800-report fit also covers 0/100 on that last shared bin.
The two fits therefore share a later height-prediction failure, although its
onset depends on the training endpoint. This remains development diagnosis.
The [training-only innovation check](prediction-observed-development/TRAINING_INNOVATION_RESULT.md)
reconstructed both sealed 600-report covariance operators and replayed their
training costs. Each leaves a fitted height-error lag-one correlation of about
0.825 after whitening; the overall whitened RMS is 0.063. These are
descriptive warnings, not calibrated rejection statistics after fitting 26
parameters. Neither later receiver positions nor reserved ESA flights entered
the check.
The [saved local-fit audit](prediction-observed-development/TRAINING_LINEAR_REFERENCE.md)
then verifies that both Jacobians have all 26 local calibration directions,
neither fit is bound-active, and the cost is only 7.15 versus a 1,774 linear
known-covariance reference. It strengthens the error-law warning without
making a formal nonlinear test or using later positions.
The [matched known-answer control](prediction-observed-development/FIT_ADJUSTED_CONTROL_RESULT.md)
then generated two separate 900-second records and fitted both supplied error
laws to each, for four numerically passing fits. Their costs were 1,781.054
and 1,814.957, about 250 times the observed ESA development cost. Every
generated fit reached calibration bounds, so the interior linear reference
does not apply directly. The two-recording control did not reproduce the tiny
observed cost and cannot calibrate its tail probability. The next development
gate is the generated boundary behavior and the mismatch between very small
observed training error and later height-prediction failure. All seven ESA
confirmation groups remain reserved.
The [saved boundary audit](prediction-observed-development/FIT_ADJUSTED_BOUNDARY_REPORT.md)
projects the active calibration directions out of each saved fit without
refitting. Removing all active limits would lower local linear cost by 1.477
or 3.647, far smaller than the roughly 1,800 generated-versus-observed cost
gap. The audit does not exclude a different nonlinear optimum or qualify the
observed error law; the scientific decision remains abstain.
The [saved residual comparison](prediction-observed-development/FIT_ADJUSTED_RESIDUAL_REPORT.md)
then finds generated fitted errors near unit whitened RMS on each axis, versus
0.063 overall on the ESA development recording. The ESA fitted height error
remains correlated at lag 20 while the generated height errors are near zero
there. No refit or later receiver position was used; the cause and observed
error law remain unresolved.
The [saved generated-versus-recorded rate comparison](prediction-observed-development/GENERATED_RATE_COMPARISON.md)
uses the two sealed generated IMU inputs and the historical ESA rate-variation
artifact. Recorded rate contrasts are much larger at the shortest span, but
aircraft motion and vibration remain mixed with sensor behavior. No original
or reserved data, later receiver values or new fits were used.
The [saved known-answer forecast score](prediction-observed-development/FIT_ADJUSTED_FORECAST_REPORT.md)
reconstructs analytic truth to nanometre precision and scores the four sealed
generated forecasts without refitting. Future horizontal RMS is 50.47 m for
increment-error truth and 84.35 m for point-error truth, nearly unchanged by
which candidate error law was fitted. Both generated controls remain
predictively inadequate under these settings; cause and uncertainty coverage
are unresolved.
The [known-calibration noisy-stream control](prediction-observed-development/ORACLE_NOISY_REPORT.md)
completed both frozen tasks after a passing two-second clean preflight and
recovery qualification. Supplying the true starting state and calibration did
not remove future drift: horizontal RMS was 59.66 m for increment noise and
637.12 m for point-rate noise, compared with 50.47 m and 84.35 m after fitting
on the same streams. This isolates a prediction failure that remains even
with known calibration; it does not identify its cause or qualify coverage.
The [matched long clean forecast](prediction-observed-development/ORACLE_CLEAN_REPORT.md)
then passed its one-task freeze and stayed close to analytic future truth:
0.035 m horizontal and 0.322 m vertical RMS. The large drift in the noisy
controls appears only after injecting IMU errors in this software setup.
The subsequent component controls are recorded below; no recorded-aircraft
error law follows from the clean comparison.
The [saved increment comparison](prediction-observed-development/ORACLE_NOISE_DIAGNOSTIC.md)
reconstructs the clean input once and compares it with both archived noisy
inputs without a new native forecast. Signed body-axis angle differences total
up to 0.022° over 900 seconds; they do not by themselves explain the position
drift. The [four channel forecasts](prediction-observed-development/ORACLE_CHANNEL_REPORT.md)
then isolate gyro and accelerometer increments on the same two draws. Gyro-only
horizontal RMS is 75.71 m and 651.36 m; accelerometer-only RMS is 17.41 m and
19.83 m. Gyro errors dominate horizontal drift here. White noise and changing
bias are still mixed in those forecasts, and the two draws do not establish a
population law. A [saved component reconstruction](prediction-observed-development/ORACLE_NOISE_COMPONENTS.md)
exactly reproduces both archived IMU streams from seeded white-error and
changing-bias arrays. It prepares a matched component forecast without
claiming their position effects from input sums alone. The subsequent
[four-task gyro component study](prediction-observed-development/ORACLE_GYRO_COMPONENT_REPORT.md)
passes all four sealed forecasts. With exact accelerometer data, the increment
draw gives 181.49 m horizontal RMS from white gyro noise and 242.77 m from
changing gyro bias; their signed horizontal errors strongly oppose each other
(cosine −0.977), and the combined gyro error gives 75.71 m. The point draw
gives 673.30 m and 300.31 m separately, versus
651.36 m combined. These are fixed generated draws, not the recorded IMU's
error law or qualified prediction intervals. No reserved group was opened.
The [matched 900-second error-scale calculation](prediction-observed-development/ORACLE_MATCHED_SCALE_REPORT.md)
completed both sealed tasks with 541,800 charged native steps. Both declared
synthetic laws predict about 350.7 m horizontal and 14.6 m vertical RMS scale
for future physical position. The two saved realizations instead have 59.7 m
and 637.1 m horizontal RMS, and 31.9 m and 7.1 m vertical RMS. This shows why
two fixed draws cannot establish coverage or select an error law for the
recorded ESA flight.
The [saved horizon comparison](prediction-observed-development/ORACLE_HORIZON_REPORT.md)
uses no new native call. With all 600 earlier synthetic receiver reports, the
expected horizontal RMS scale grows from 0.89 m over 60 withheld seconds to
17.59 m over 300; without earlier updates it is 350.70 m over 300. The
separately sealed 800-training generated study gives 2.71 m over the next
120 seconds, close to 2.70 m from the 600-training study. These are
assumption-based scales, not observed-flight coverage. The
[retrospective ESA development check](prediction-observed-development/RECORDED_HORIZON_DIAGNOSTIC.md)
finds 0.28, 1.94 and 14.25 m horizontal RMS over the first 120, 200 and 400
withheld reports from the already sealed fit. Neither table qualifies a new
window or observed-aircraft uncertainty law.
A [local forecast control](prediction-observed-development/FORECAST_AMBIGUITY_CONTROL.md)
uses no aircraft data or fit. It constructs identical recorded IMU and
training-position inputs whose possible future paths separate by 2.79 m
under an illustrative changing sensor error. That example sets no measured
instrument bound or coverage probability.
The [metadata-only short-block selection](esa-short-block-development/README.md)
then freezes 800 training and 120 future reports in each of the three
previously chosen, nonoverlapping development windows. Its three source-bound
checks and independent receipt verification pass. It reads no measurement,
runs no fit and leaves all seven confirmation groups closed. Error-law
qualification still gates observed preparation and fitting.
The [chronology note](esa-short-block-development/INTERPRETATION.md) records
that the 120-report duration was selected after the first window's forecast
errors were known. The three additional windows are exploratory development,
not independent validation of the revised duration.
The [400/120 earlier-origin preflight](prediction-observed-development/ROLLING_ORIGIN_400_PREFLIGHT.md)
then verifies a separate cut in the already opened first development window:
400 training receiver reports, 120 withheld reports and 155,868 IMU packets
through the prediction end. Fit inputs exclude the later positions. This is
input preparation, with zero fits and no reserved group opened. The subsequent
two-task study passed nine source-bound software checks, and its separate
five-check task-recovery qualification and frozen policy verify. Both fits
[sealed](prediction-observed-development/ROLLING_ORIGIN_400_FIT_RESULT.md)
with passing numerical checks in eight evaluations each and no active
calibration bounds. The separate
[conditioning plan](prediction-observed-development/ROLLING_ORIGIN_400_CONDITIONING_PLAN.md)
passed eight focused checks and five generic recovery checks. It was
prepared from those sealed fits; no later receiver position entered its
inputs. Both conditioning tasks sealed with exact training-cost and
covariance-normalization replay. The [withheld score](prediction-observed-development/ROLLING_ORIGIN_400_CONDITIONAL_RESULT.md)
is 0.56 m horizontal and 0.17 m height RMS after conditioning on the first
400 receiver reports, versus 5.38 m raw horizontal RMS. Both assumed error
laws give nearly the same result. All nominal ranges cover the 120 reports,
but strong time correlation prevents treating them as independent coverage
checks. This selected development window does not calibrate the error law or
establish longer-period physical adequacy.
The [fit evidence](prediction-observed-development/rolling-origin-400-fit-evidence/README.md)
and [conditioning evidence](prediction-observed-development/rolling-origin-400-conditioning-evidence/README.md)
preserve the frozen inputs, source snapshots, charges and completion receipts.
Self-contained [fit](prediction-observed-development/rolling-origin-400-fit-evidence/bundle.zip)
and [conditioning](prediction-observed-development/rolling-origin-400-conditioning-evidence/bundle.zip)
bundles allow verification without the shared archive catalog.
The separate [saved timing check](prediction-paired-law/SAMPLING.md) uses 239,863
earlier ESA development intervals and finds a point-to-increment accumulated
white-noise variance ratio of 1.00000469. The archive's packet-time variation
does not materially separate these synthetic law settings.
The [saved six-channel dependence check](prediction-observed-development/RECORDED_CHANNEL_DEPENDENCE.md)
uses the sealed 239,864-sample ESA training interval and verifies its 55 frozen
source files from the archive. The largest gyro/accelerometer same-time
contrast correlation is gyro Y against force X: −0.628 at a 6.7 ms span,
−0.360 at 20 ms, −0.239 at 0.2 s and −0.747 at 2 s. This shows common
short-time variation but cannot assign it to aircraft motion, vibration,
processing or sensor error. It performs no new fit and opens no reserved data.
The [analytic attribution control](prediction-observed-development/ERROR_ATTRIBUTION_CONTROL.md)
constructs 9,000 sampled IMU readings and 31 one-second receiver reports.
Real pitch/translation vibration and correlated sensor error produce exactly
the same reports, despite different true angular motion. Four focused tests
pass. This is a software counterexample to assigning the recorded correlation
to one cause from those observations alone, not a model of the ESA aircraft.
The [bound-aware affine prediction control](bounded-calibration-prediction/README.md)
passes nine local checks and retains calibration uncertainty at active limits.
Its mathematical guarantee is limited to an affine model with known Gaussian
error. A seven-check helper unions intervals from all supplied matched laws
instead of selecting one by a nearly tied training score; it does not verify
that any law applies to aircraft. The [24-case nonlinear technical release](bounded-calibration-prediction/NONLINEAR_RESULT.md)
completed every case and passed 23 combined numerical/accuracy gates; all 24
withheld-position accuracy screens passed. Bounded intervals contained all
tested coordinates but are broad and do not establish calibrated aircraft
coverage. One numerical failure remains preserved.
All comparisons have active calibration bounds, and
fixed-parameter marginal intervals under-cover both withheld targets. Every
scientific decision abstains; bound-aware uncertainty remains to be qualified.
The [finite timing probe](bounded-calibration-prediction/TIMING_PROBE_RESULT.md)
audits eight saved objective points from the one failed generated fit. Timing
alone follows its tangent, so the coupled calibration/timing step is the
remaining numerical question. The probe's wrapper failed; its terminal label
and the original combined 23/24 result remain unchanged.
The [two-seed method check](bounded-calibration-prediction/INDEPENDENT_SEEDS_RESULT.md)
then completed all 48 new generated cases: 48 numerical and 48 withheld-position
accuracy passes. Both target bounds contained all 5,760 tested coordinates.
Two independent draws per condition do not calibrate 95% coverage or justify
an aircraft threshold; every scientific decision abstains.
A separate exact-period 200 Hz control passes native fitting under both clock
labels. A deterministic packet-time disturbance yields different forecasts
with the same generated IMU increments and receiver reports; it does not
measure the archive's timing error.
A generated Z gyro boundary case retains matched receiver observations and
noise against the interior case and reaches a native forecast. Its later-error
coverage is still untested.

[Complete prediction calibration](prediction-calibration-host-20261030/INTERPRETATION.md):
all 7,176 fits across 299 independent seed families passed numerical and position
checks in 151.7 hours. The saved-data audit and publication replay agree exactly.
A finite prediction-error threshold is available for the frozen simulated
population. [Independent validation](HOST_PREDICTION_STATUS.md) saved 3,750
passing fits before a reboot interrupted four charged starts. Its frozen
complete-cohort rule does not permit a validation claim.

[Reboot-safe continuation](VALIDATION_CONTINUATION.md): the 3,750 original fits
and all 260 frozen sources verify. A first technical release stopped after 93
software errors caused by a deadline adapter mismatch; its sealed results are
retained but are not model evidence. The corrected release completed all 594
remaining fits. An [independently replayed report](prediction-validation-continuation/README.md)
verifies 4,344 complete fits and a passing generated-data coverage check across
181 simulated cases. The original run remains interrupted.

[Fresh host-managed calibration preparation](host-calibration-preparation/README.md):
154 software checks pass, and the 7,176-start freeze is independently verified
with zero charged fits. The reporting repair and interruption policy are explicit;
the numerical method is unchanged. See [current execution status](HOST_PREDICTION_STATUS.md).

[Initial execution recovery](execution-recovery/README.md): all 61 source-bound software
checks passed, including 26 new tests for interrupted starts, leases, seals, charge
preservation and archived completion. The checker cannot launch or retry work.
The [host-service lifecycle control](execution-host-service/README.md) also
completes all eight heartbeats after its submitting command exits. This qualifies
that execution arrangement for normal command exit, not host reboot or logout.
The separately frozen fresh release is tracked in the current status above.

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
[Next analyses](NEXT_STEPS.md) · [Reproduce these studies](REPRODUCIBILITY.md).

**Latest completed optimizer qualification:** [the local timing method passes the full matrix](timing-local-matrix/INTERPRETATION.md).
All 48 development fits and all 24 paired-start comparisons pass; four original
input/error bindings reproduce exactly. The run finishes in 65.7 minutes after
203 source-bound software checks. Earlier failures remain recorded.

**Earlier calibration outcome:** the [local-timing release stopped at its numerical gate](prediction-calibration-timing/INTERPRETATION.md).
It returned 348 of 7,176 planned starts in 6.82 hours: 344 passed, two failed
timing-cell stability and two stopped cooperatively. All 346 complete forecasts
met the position-error limits. No calibration threshold was established, and
validation was not launched. The saved linear verification proposals are the
next diagnostic target; these generated cases do not change the aircraft findings.

**Latest diagnosis:** [four saved linear calculations](timing-linear-baseline-diagnosis/README.md)
reproduce worsening proposals in both failed cases; the matched controls do not
worsen. Their result-schema rejection is preserved, and the saved calculations
were independently checked without a rerun. A correction still needs independent
known-answer qualification at that stage; no native calculation or fit was performed.

**Linear correction checked:** [feasible initialization](timing-linear-anchor-check/INTERPRETATION.md)
passes all 24 independent convex controls and four matched saved matrices after
56 source-bound checks; 90 related software tests also pass. The previous
method fails ten controls. The [new complete-optimizer qualification](timing-feasible-optimizer-qualification/INTERPRETATION.md)
now passes all 36 fits, eight probes and nine start groups in 27.8 seconds after
148 software checks. The [six-case native trial](timing-feasible-native-regression/INTERPRETATION.md)
now passes all fits, three start pairs and six original-input replays in
10.6 minutes after 338 pre-execution software checks. A reporting-only repair
passes 339 checks without repeating fits. The [closed matrix](timing-feasible-matrix/INTERPRETATION.md)
now preserves 44 passing fits, 22 complete start pairs and four runtime-interrupted
starts after 51.0 minutes. All 1,239 publication artifacts and 28 native assets
verify, and the archived audit replays identically. A
[separate four-case follow-up](timing-matrix-completion/INTERPRETATION.md)
passes all four fits and both start pairs in 4.6 minutes after 364 software
checks. The [combined audit](timing-matrix-combined/README.md) qualifies all
48 computational cases, 24 start pairs and four original replays after 16
assembler checks, with all 241 shared execution sources and environment
unchanged. Original interrupted labels remain preserved.
At that earlier stage, the calibration threshold was unavailable.

**Previous calibration outcome:** the [feasible-anchor release](FEASIBLE_PREDICTION_STATUS.md)
stopped after an execution interruption at 38.7 hours. It saved 1,813 numerically
passing fits and four interrupted charged starts; no numerical failure was
saved. Both starts of one required setting are unavailable. The remaining
5,359 starts are closed unused; that release established no threshold and its
validation did not start. The [independent audit](prediction-calibration-feasible/INTERPRETATION.md)
confirms all 1,813 completed forecasts pass the position-error checks too.
All 42,064 publication artifact hashes verify; the archived report replays
identically. The
[preparation snapshot](feasible-calibration-preparation/README.md) preserves
the original plan; the 253 sources and numerical environment remain unchanged.

**Earlier closed calibration outcome:** [the compensated run stopped at its numerical gate](prediction-calibration-compensated/INTERPRETATION.md).
Of 909 returned starts, 904 passed, two failed and three stopped cooperatively;
all 906 completed forecasts met the position-error screens. No uncertainty
threshold was established, so validation for that release did not start. These are generated
measurements, not additional flights or Earth-model votes.

**Diagnostic sequence:** [both sides of the timing boundary were checked](saved-timing-boundary/INTERPRETATION.md).
All four saved calculations replay exactly and all 18 local derivative checks
agree. The [interval-step component](saved-timing-cell-proposals/INTERPRETATION.md)
now produces all 18 bounded linear proposals. Their
[physical evaluation](saved-timing-cell-native/INTERPRETATION.md) passes the
original cost, stationarity and actual position-change screens for all 18.
The run takes 2.6 minutes after 103 software checks, with no fitting or relabeling.
A complete interval-aware optimizer remains to be qualified.
Its [analytical qualification](timing-stopping-qualification/INTERPRETATION.md)
now passes 32 complete fits, eight direct controls and all eight comparisons
between starts. These checks add no aircraft observations and change no earlier result.
The [four native regressions](timing-optimizer-regression/INTERPRETATION.md)
finished without qualification: all inputs replay, but final cost stability
fails. A separate curved-minimum control motivates the
[local timing qualification](timing-local-qualification/INTERPRETATION.md).
All 36 fits, eight direct controls and nine starting-point comparisons pass
after 175 software checks. The [new four-case simulator trial](timing-local-native-regression/INTERPRETATION.md)
passes all four fits, both start comparisons and all original input replays
in 10.7 minutes after 189 software checks. The [48-case matrix](timing-local-matrix/INTERPRETATION.md)
now passes all fits, all 24 start comparisons and four original input replays
in 65.7 minutes after 203 software checks. Optimizer qualification is complete;
the [new calibration release](prediction-calibration-timing/INTERPRETATION.md)
subsequently stopped after 348 returned starts despite passing its 285
source-bound software checks. Its 227-source execution freeze and all outcomes
are preserved. Independent validation still requires a finite, audited handoff.

## From recordings to the complete comparison

| Study or stage | What it added |
|---|---|
| [Reference inspection](research-next-stage-20261006/airborne-sample-ilvis0/README.md) and [physical decoding](ilvis0-physical-validation-20261007/README.md) | Recovered intact packet framing, raw angle/velocity increments, units, signs and embedded receiver output. |
| [Other IMU configurations](ilvis0-imu21-assessment-20261007/README.md) and [IMU6 checks](ilvis0-imu6-cross-date-20261007/README.md) | Kept instrument-specific conversion hypotheses separate rather than assuming one format for every file. |
| [Recording screening](ilvis0-retention-84-20261007/README.md) and [motion screening](ilvis0-motion-61-20261007/README.md) | Recorded keep, reject and unsupported outcomes; 232 originals were retained. |
| [Receiver extraction](ilvis0-observation-20261007/README.md) and [GPS checks](ilvis0-gnss-v2-20261007/README.md) | Separated raw inertial observations and primary-receiver positions from the fused navigation solution. |
| [Primary-receiver precision inventory](ilvis0-trimble-position-precision/recorded-inventory/README.md) | Checked the binary receiver stream in all 53 selected recording files. Fifty-two pass strict decoding and same-receiver position checks, yielding 145,446 receiver-reported precision records; one has unsupported interior bytes. These are not independently calibrated position errors or Earth-model fits. |
| [Overlapping primary receivers](ilvis0-receiver-overlap/recorded-study/README.md) | Completed all eleven pairs with accepted streams: 25,890 exact shared epochs and 0.202 m median later horizontal disagreement after an earlier-only fixed offset. The differences are strongly correlated; common GNSS errors and antenna relationships remain unknown. |
| [Withheld errors versus receiver precision](receiver-precision-holdout/README.md) | Matched every saved prediction epoch on three preselected recordings to the same receiver's precision report. Twenty-eight of 36 settings have a training-cost-selected numerical start; eight abstain. Seven of nine specified-field globe settings pass the pilot's uncalibrated accuracy screen, while their typical later errors still exceed receiver-reported precision. Smooth time trends dominate centered later errors; their cause is undetermined. No new fits or significance claim. |
| [Earlier-only residual extrapolation](prediction-drift-control/README.md) | Tested a fixed mean and straight-line correction from the final two training minutes on all 28 qualified pilot settings; eight settings remain abstentions. The line worsens seven of nine specified-field globe forecasts and leaves both alternatives hundreds of metres off despite improvements. This diagnoses one simple drift rule; it does not change the original fits or calibrate uncertainty. |
| [Prediction error-law software qualification](prediction-error-law-qualification/README.md) | Twelve source-bound checks verify training-only fixed-law scores and fitted-mean forecast scales. A one-epoch case has equal fixed-mean likelihoods, while fitted-mean forecast scales differ tenfold; its profiled law score abstains for lack of residual degrees of freedom. Nonlinear and observed coverage studies remain open. |
| [Independent linear error-law control](PREDICTION_ERROR_LAW_PLAN.md) | Four development software checks pass. The truth generator draws separate gyro, accelerometer and receiver streams; 20,000 short histories agree with an independently built covariance, and 300 seeded histories give plausible withheld-receiver coverage under the correct fixed law with an earlier-fitted mean. This does not establish full-aircraft or observed-data coverage. |
| [Finite known-answer error-law identification](prediction-known-answer-identification/RESULT.md) | A corrected, source-bound four-task trial completed 400 generated histories and all 404 charged operations after the first allowance's result-schema failure was preserved. An earlier-only rule made 166 provisional single-law choices, abstained 234 times and chose wrongly five times. The true supplied law covered 3,764/4,000 withheld receiver epochs with nominal 95% intervals. Full-aircraft and observed coverage remain open. |
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
| [Gyro-free force covariance helper](ilvis0-measurement-contribution/CHANNEL_CONTROLS.md) | Eight checks pass, including a nonlinear replay with correlated errors. A supplied receiver covariance is propagated through candidate force magnitudes while preserving error shared by overlapping windows; near-zero force abstains. This linearized software result does not calibrate receiver error or make an aircraft decision. |
| [Receiver-only joint bridge](ilvis0-measurement-contribution/SUPPORT_POLICY.md) | Five focused checks pass. Timed GPS fixes select common windows for all three models and produce force magnitudes with receiver covariance shared across windows and candidates; recorded-data decisions remain open. |
| [Structured force-error projection](ilvis0-measurement-contribution/CHANNEL_CONTROLS.md) | Ten checks pass: six against the dense projection reference and four connecting GPS-selected windows, including transformed coordinates and a 200-fix history. It avoids a dense full-record covariance; receiver-error calibration, selection uncertainty and connection to the earlier matched accelerometer comparison remain open. |
| [Receiver-only support selector](ilvis0-measurement-contribution/SUPPORT_POLICY.md) | Twenty-one software checks pass for common window selection and dated GGA motion derivation with explicit gap and speed limits. The WGS84 chart is for screening only; recorded thresholds and error coverage remain open. |
| [Receiver gap-block inventory](ilvis0-receiver-gap-inventory/README.md) | All 53 preselected stretches were screened from saved primary-receiver positions: 52 have one uninterrupted block each under the 1.5-second gap rule; one retains its prior strict-decoder failure. The public tables preserve original receiver row ranges. No IMU fit was made. |
| [Enhanced-position force bridge](ilvis0-measurement-contribution/SUPPORT_POLICY.md) | Three new and 31 existing support/bridge checks pass. The software uses the receiver's GPS timestamps and GNSS velocities while retaining its separate provenance; no recorded block or IMU channel has been fitted by this path. |
| [Receiver-only window inventory](ilvis0-receiver-support-inventory/README.md) | Under a fixed GPS-only rule, 2,194 of 2,365 target times across 52 decoded stretches have local support; all 52 have at least one. The prior decoder failure remains. All 171 unsupported targets exceed the declared receiver vertical-rate variation limit. No IMU or Earth-model fit was used. |
| [Receiver-window threshold audit](ilvis0-receiver-support-inventory/MARGIN_AUDIT.md) | A hash-bound saved-data report measures the distance of all 7,095 candidate windows from the fixed vertical-motion limit. Of 2,194 chosen windows, 398 are within 0.10 m/s. This describes selection sensitivity, not observed receiver error or changed flight eligibility. |
| [Paired receiver-window check](ilvis0-receiver-window-pairs/README.md) | All eleven sealed overlapping receiver pairs passed a fixed motion-window comparison. At 490 common times, both receivers accepted 456, both rejected 27 and disagreed seven times. Both selected the same width at 423 of 456 jointly accepted times. This is relative repeatability, not absolute receiver-error calibration; zero IMU/model calls. |
| [Receiver-window stability check](ilvis0-measurement-contribution/WINDOW_STABILITY_RESULT.md) | A saved-only replay of all 2,365 original target times certifies 1,580 chosen windows unchanged under illustrative ±0.05 m/s speed/climb and ±0.05° course errors, and 1,111 under ±0.10 m/s with the same course range. Uncertified choices are not observed flips. No IMU or Earth-model fit was used. |
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
| [Native training error adapter](integrated-noise-covariance/training-adapter-qualification/README.md) | All 56 checks pass across three models and both input formats, retaining every calibration column and earlier-only conditioning without dense whole-record covariance. Nonlinear prediction accuracy and calibration at bounds remain unqualified. |
| [Efficient native-work accounting](integrated-noise-covariance/prepaid-native-qualification/README.md) | All 112 bookkeeping checks pass; bounded blocks avoid per-packet database transactions while preserving full interruption charges, cooperative stops and operation counts. No numerical speedup or new flight result is claimed. |
| [Sampled-rate error generator](integrated-noise-covariance/rate-point-input-qualification/README.md) | All 54 checks pass, preserving shared endpoint errors, cross-axis covariance and identical earlier prefixes. This qualifies a declared synthetic input law for later nonlinear tests, not actual sensor noise. |
| [Complete short noisy protocol](integrated-noise-covariance/short-native-protocol-qualification/README.md) | All 128 software checks pass. Twelve two-second cases return accurate raw and conditional forecasts, but retain numerical nonconvergence and unidentified calibration. Qualifies interface behavior and physical-position target handling, not long-duration validation. |
| [Two-minute noisy calibration and prediction](structured-noisy-training/README.md) | Verified: all 24 raw and conditional forecasts meet the physical screen; 20 pass numerical checks. Later horizontal RMS is 1.84–2.08 m, but all calibrations reach bounds and uncertainty is unsupported. Does not replace the earlier twenty-minute failure or add aircraft evidence. |
| [Saved calibration and stopping diagnosis](structured-noisy-diagnosis/INTERPRETATION.md) | All planted sensor settings are inside the bounds, but gravity and vertical accelerometer effects nearly cancel. Both starts agree closely in cost. Four failures miss only cost stability. No new fits or changed labels; bounded uncertainty is the next gate. |
| [Bounded accumulated-error interface](integrated-noise-covariance/bounded-state-qualification/README.md) | Passes 58 software checks, including 20 new adapter cases and independent dense references. Preserves calibration at boundaries and all unknown directions. Missing nonlinear error allowances remain unsupported; no aircraft result or confidence claim is added. |
| [Native bounded uncertainty](integrated-noise-covariance/native-bounded-reference-qualification/README.md) | All 24 native controls pass after 69 interface checks. [Exact arithmetic](integrated-noise-covariance/native-bounded-numerics/README.md) identifies an unstable dense-reference whitening solve; the original 22/24 failure remains unchanged. Nonlinear coverage is still unqualified. |
| [Known-calibration noise benchmark](noisy-prediction-benchmark/README.md) | All four settings verified. Calculated horizontal error scales grow from 0.52 m at two minutes to 33.77 m at twenty minutes, even with known calibration and starting state. These assumed-noise calculations add no aircraft evidence and leave accuracy limits unchanged. |
| [Nonlinear noise approximation](noise-nonlinearity/README.md) | Complete: both short settings pass; both longer settings retain failures. Four of 64 matched controls miss the fixed limit, all in height. The [saved diagnosis](noise-nonlinearity/remainder-diagnosis/README.md) locates small quadratic effects, with maximum vertical departures of 7.3 cm and 4.4 cm. Calibration is known here; fitted-calibration uncertainty remains open. |
| [Scores after calibration fitting](fitted-prediction-scores/INTERPRETATION.md) | Reuses all 24 saved starts without refitting: 20 numerical passes and ten training-selected comparisons. Maximum error/noise ratios are 5.29–6.25. These are generated checks sharing one seed, not confidence levels or new Earth-model evidence. |
| [Fresh-draw fitting and prediction](independent-noisy-training-pilot/INTERPRETATION.md) | All 48 fits pass numerical and position-error checks; a 17-check audit verifies every saved outcome. The 24 training-selected forecasts have 2.49–3.78 m horizontal RMS. All selected calibrations reach a bound, and their uncertainty is still missing from the reported noise scores. Two independent seeds do not establish coverage. |
| [Prediction-calibration bookkeeping](prediction-score-qualification/calibration-targets-qualification/README.md) | All 30 deterministic checks pass. Counts independent seed families, preserves unavailable predictions, rejects reused seeds and separates conservative calibration from the validation target. The [execution interfaces](prediction-score-qualification/execution-qualification/README.md) now pass another 32 checks. |
| [Independent prediction calibration](prediction-calibration/README.md) | Stopped cooperatively after 1,686 returned starts: 1,683 qualified fits, two numerical failures and one interrupted start. Both starts failed one required setting, preventing a finite threshold; validation was not launched. |
| [Bounded calibration failure review](prediction-phase-review/README.md) | Eight saved records isolate the cost-stability check: position changes and stationarity pass, but relative cost change exceeds its frozen limit. No refits or new noise draws; all failed labels are preserved. |
| [Four-point stopping diagnostic](prediction-stopping-consistency/INTERPRETATION.md) | Exact repeatability preserves two passes and two failures. All 105 derivative columns are checked at three step sizes; timing and small-step precision discrepancies appear in successful controls too. No new nonlinear fits. |
| [Small timing and rounding controls](timing-precision-controls/INTERPRETATION.md) | Seven cases pass after 13 software checks and two reporting checks. Independent formulas reproduce different slopes at packet boundaries; a longitude-origin change exposes lost gyro sensitivity. Saved interval hashes verify exact packet-end queries in all four earlier examples. No failed fit is relabeled. |
| [Matched saved-point arithmetic](saved-point-timing-arithmetic/INTERPRETATION.md) | Four tasks finish after 42 software checks. The inward timing branch passes 12/12 timing comparisons; gyro Z-offset remains 0/12 with either coordinate setting. Baseline costs replay exactly, all columns remain, and no fit is rerun. |
| [Compensated coordinate controls](coordinate-precision-controls/INTERPRETATION.md) | All six compensated origin/axis cases meet the fixed precision tolerance, compared with three original and four longitude-only cases. The 46 software checks retain all physical candidates and calibration columns. Complete saved-history accuracy and stopping behavior remain to be tested. |
| [Complete compensated saved-point check](saved-point-coordinate-precision/INTERPRETATION.md) | All 315 derivative comparisons and four original stopping probes pass at unchanged saved parameters, after 99 software checks. No optimizer runs or original labels change; optimization qualification follows. |
| [Compensated optimizer qualification](compensated-optimizer-qualification/INTERPRETATION.md) | All 48 generated fits, 24 paired-start comparisons and four original input/error replays pass in 30.3 minutes after 93 software checks. The original limits and failed labels remain; no uncertainty threshold is produced. |
| [Fresh calibration outcome](prediction-calibration-compensated/INTERPRETATION.md) | After 126 preflight checks, 909 starts return in 9.58 hours: 904 pass, two fail numerical cost stability and three stop cooperatively. All 906 completed forecasts meet position-error screens, but no uncertainty threshold was established and validation for that release did not start. |
| [Saved clock-boundary review](prediction-clock-boundary-review/README.md) | After 22 software checks, exact clock hashes verify that the two failed fits place all receiver queries within about 304 ns and 3.8 ns of internal integration boundaries. No new fits, noise draws or native calls; proximity guides a diagnostic without proving the cause. |
| [Saved linear timing corrections](prediction-linear-timing-review/README.md) | After 26 software checks, four charged linear solves reproduce all saved probe metrics. Both failures propose crossing all 119 query boundaries; both successful controls cross none. No new nonlinear fits or native calls; two-sided timing behavior remains to be tested. |
| [Known-answer timing-kink controls](timing-kink-controls/README.md) | Four analytical checks demonstrate that the unchanged smooth stability rule can reject two exact nonsmooth minima despite correct derivatives. Smooth controls behave as expected. This proves a numerical limitation, not its cause in the calibration failures. |
| [Two-sided timing and correction diagnostic](saved-timing-boundary/INTERPRETATION.md) | All four saved inputs and complete Jacobians replay exactly; all 18 within-interval timing checks agree. The 78 evaluations finish in 6.7 minutes. Crossing corrections nearly cancel timing/calibration effects; no original fit label changes. |
| [Steps constrained to timing intervals](saved-timing-cell-proposals/INTERPRETATION.md) | After 26 independent software checks, all 18 saved-matrix solves succeed with every nuisance column and physical bound retained. Both sides and all spacings propose the same failed-case boundary; physical costs are not yet evaluated. |
| [Earlier calibration phase outcome](PREDICTION_PHASE_RESULTS.md) | Publishes the earlier stopped phase, remaining uncertainty limits and prioritized follow-on work; its execution allowance remains closed. |
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
| [ESA and Wuhan data](external-imu-data/README.md) | One ESA height-gravity development setting now completes an adequate three-model prediction comparison; numerical stopping diagnosis follows. Earlier failures remain preserved. Wuhan remains at inspection and source-assessment stage. |
| [ESA receiver-only selection](esa-development-selection/README.md) | The first frozen policy admits no stretches from development recording 187. Motion exclusions dominate; every rejected run and epoch reason is preserved, with no model fitting or protected-outcome inspection. |
| [ESA rate/body qualification](esa-rate-qualification/INTERPRETATION.md) | All 48 generated identities pass for analytic quadrature and local changing-axis/force bounds. This initial check left actual sampling/processing and geographic propagation open; later geographic controls are listed below. It changed no selection or model result. |
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

[Eight-minute input and clock checks](ilvis0-recording-duration-controls/INTERPRETATION.md): all six cases pass in 109 seconds, preserving the original prefix and exact API agreement with an explicitly expanded ±1-second clock bound; full-horizon uncertainty remains open.

[Staged training controls](ilvis0-staged-training-controls-v2/INTERPRETATION.md): all six small cases pass in 94 seconds, retaining every earlier observation constraint and checking the prediction endpoints independently; the separate full-history usefulness test follows.

[Full-history prediction feasibility](ilvis0-long-staged-feasibility-v2/README.md): all six numerical cases finish and retain the known answers, but none produces useful ranges. The bounding method needs improvement; these generated ranges are not measured aircraft errors.

[Saved prediction-budget audit](ilvis0-proof-budget-audit/README.md): all six
saved cases pass their hash and arithmetic checks. The position-reconstruction
term accounts for over 99.999% of the reported unshared allowance in every axis.
This identifies the next diagnostic target without qualifying the prediction ranges.

[Calibration-box audit](ilvis0-calibration-box-audit-v2/README.md): all six saved
projections pass exact checks. Only the initial vertical offset and clock offset
get narrower individual intervals; orientation and sensor calibration remain
broad. The prediction method needs to preserve coupled parameter information.
The first wrapper's six input-check failures remain linked and unchanged.

[Compact calibration references](ilvis0-static-reference-controls/README.md):
all six saved references reproduce exactly from 249,591 bytes of verified inputs
in 1.61 seconds. No trajectory history is loaded. This qualifies the compact
input path for the [static coupling comparison](ilvis0-static-training-coupling/README.md),
not the prediction ranges or real observation errors.

[Static calibration coupling](ilvis0-static-training-coupling/README.md): all 54
checks pass in 4.85 minutes. Keeping all eight orientation parts reduces the
reference-acceleration allowance by 3.7–7.1%, with unchanged physical bounds and
no trajectory integration. Useful prediction ranges remain unqualified.

[Complete prediction-width audit](ilvis0-prediction-width-budget-v2/README.md):
all six cases and 18 exact checks pass in 1.64 seconds. Reconstruction allowances
contribute 77–91% of total width; rounding is negligible. This identifies the
next numerical target without changing the failed prediction labels. The first
audit's four rounding-convention rejections remain preserved.

[Tighter remainder over complete histories](ilvis0-long-remainder-feasibility/README.md):
all six cases pass numerical checks and retain the known answers in 3.7 hours,
but none meets the unchanged 20/20/50 m targets. Smaller ranges remain much too
wide; no aircraft prediction fits follow. The [next diagnostic](ilvis0-long-remainder-feasibility/NEXT_PLAN.md)
will distinguish loose bounds from possible ambiguity in the training data.

[Nonlinear training-compatible predictions](ilvis0-nonlinear-witnesses/README.md):
twelve searches complete in 22.4 minutes, spending all 396 native batches.
Five pairs return their starting calibration; only one yields a different
accepted point, with no target violation. This exposes a search limitation,
not zero uncertainty. Saved first steps motivate [feasible-step qualification](ilvis0-nonlinear-witnesses/NEXT_PLAN.md).

[Combined receiver/IMU error operator](ilvis0-joint-error-operator/README.md): 15 focused checks agree with the dense reference through 438 seconds while retaining training/future correlation and all 27 columns; the assumed error law is not yet established for aircraft recordings.

[Simultaneous observation allowances](ilvis0-gaussian-allowances/README.md): 15 component checks and all six small staged model/processing cases pass, sharing one probability budget across training and future errors without assuming independence; aircraft noise-law justification remains open.

[Clock-aware variance bounds](ilvis0-joint-variance-bounds/README.md): 12 checks and all six updated staged integration cases pass with exact variance arithmetic over the declared clock interval; the error law remains an explicit assumption, and the long-record model-prediction test is unchanged.

[Conditional force remainder](ilvis0-conditional-remainder/README.md): a checked algebraic bound reduces the first pair's force Taylor remainder from 53.2 to about 6.1 m/s² without changing calibration bounds or shared coefficients.

[Conditional remainder in numerical integration](ilvis0-remainder-native-controls/README.md): all twelve fixed controls pass in 15.3 minutes, preserving the broad calibration and clock domain, shared coefficients and every known probe. Long-record usefulness remains a separate requirement.

[Five-epoch training leverage](ilvis0-linear-leverage/INTERPRETATION.md): saved linear calculations admit 420–1,068 m of horizontal variation within the training constraints. This identifies sparse training coverage as another issue to address; no new integration or aircraft fit was run.

[Training density](ilvis0-training-density/INTERPRETATION.md): all six diagnostics pass their numerical checks; 292 training epochs narrow the linear ranges, but none meets the unchanged prediction-width targets. The next question is whether the large linear variations survive the nonlinear training constraints.

[Nonlinear training check](ilvis0-density-native-probes/INTERPRETATION.md): all twelve diagnostics complete; every proposed calibration fails the full nonlinear training constraints. This shows that the sampled large linear variations are not demonstrated nonlinear ambiguity; no aircraft fit was run.

[Shared calibration terms](ilvis0-probe-shared-map-audit/INTERPRETATION.md): saved comparisons improve for all twelve probes when the retained calibration cross-effects are included. Largest residual mismatches fall from 845 to 48 m and from 3,955 to 216 m; uncertainty bounds remain unqualified.

[Endpoint derivative check](ilvis0-endpoint-curvature/INTERPRETATION.md): the saved derivative average is worse than the shared-source expression in ten of twelve probes. It is not a replacement; the next audit isolates curvature after the existing source terms.

[Residual-source curvature](ilvis0-residual-source-curvature/INTERPRETATION.md): correcting only the error left after the known calibration terms improves all twelve probes. RMS mismatches fall from 9.07 to 0.64 m and from 45.35 to 3.28 m; a guaranteed bound with clock-boundary treatment remains necessary.

[Piecewise error allowance](ilvis0-piecewise-trapezoid/README.md): fourteen exact-arithmetic checks qualify a mathematical error allowance with explicit derivative and slope jumps. Native derivative bounds and complete clock-boundary coverage remain unverified.

[Calibrated-packet derivatives](ilvis0-calibration-path/README.md): nine checks enclose bias/gain and partial-clock derivatives through third order, including an independent power-series reference. Complete native propagation and clock-partition verification remain open.

[Rotation derivatives](ilvis0-path-jets/README.md): six checks verify exact interval arithmetic, outward dyadic rounding and noncommuting rotation derivatives through third order. Complete trajectory bounds remain open.

[Trajectory-step derivatives](ilvis0-path-motion/README.md): 48 combined checks cover geographic metrics, rotations, midpoint velocity/position updates and outward rounding. Whole-history bounds, clock/branch coverage and native execution error remain unqualified.

[Rotation-switch bounds](ilvis0-rotation-branch-bounds/README.md): three checks enclose both native rotation formulas and their local derivative jumps. Full-history propagation and floating-point execution remain open.

[Native packet adapter](ilvis0-path-native-controls/README.md): all six generated cases pass position and first-derivative comparisons across all 27 parameters; six native queries and 162 interval steps. Full-history uncertainty remains unqualified.

[Compiled derivative arithmetic](ilvis0-path-arithmetic/README.md): seven checks compare outward operations with the rational reference, including extreme scales and subnormals. The motion step and packet adapter each pass ten further local checks.

[Compiled multi-packet adapter](ilvis0-compiled-path-controls/INTERPRETATION.md): all six cases and all 27 parameter directions pass across 64 packets in 57.44 seconds. Native values and first derivatives fall inside every interval; complete-record uncertainty remains unqualified.

[Clock boundaries and residual jumps](ilvis0-clock-branches/README.md): 32 distinct checks preserve packet-boundary ownership, cumulative-time discrepancies and explicit signed jumps, including an eight-minute history. Native trajectory and execution-error bounds remain open.

[One-step ambiguity repair](ilvis0-training-repair/INTERPRETATION.md): all four linear proposals fail the unchanged nonlinear training test; an independent exact saved-position audit confirms the failures. No new feasible alternative or useful width bound follows.

[Nonlinear calibration rays](ilvis0-ray-probes/INTERPRETATION.md): all twelve smaller proposals satisfy earlier ±1 m constraints; the zero-removal north predictions span 21.75 m, exceeding the 20 m target in this generated fixture. An independent saved-position audit confirms feasibility and charges without rerunning trajectories.

[Original-observation probes](ilvis0-truth-probes/INTERPRETATION.md): six of twelve fixed calibrations satisfy the running study’s actual noisy observations; sampled north spreads are 13.33 m and 5.90 m. The independent audit does not transfer the zero-reference counterexample or claim an outer bound.

[Checked local-step controls](ilvis0-feasible-step-controls/README.md): all 36 fixed proposals completed; the step component qualified in all twelve model/processing/direction combinations. [Accepted alternatives](ilvis0-feasible-step-controls/INTERPRETATION.md) give north predictions 22.99–23.27 m apart in all six generated cases. This refutes the 20 m sparse-training target under the declared numerical guard. Aircraft uncertainty remains unqualified.

[Training cadence and accepted alternatives](ilvis0-witness-density/README.md): all 18 fixed predictions completed and preserved the original epoch values exactly. At one-second spacing, four cases exclude one common observation for the original calibration and its selected pair; two still allow it. This tests calibration ambiguity within each candidate, not Earth shape. No refitting or invented observations.

[Primary-receiver metadata availability](ilvis0-receiver-metadata/README.md): all 53 saved recording reports passed the source checks. None lists GST/GBS sentences; most stream bytes were not parsed as NMEA. The audit identifies available information, without original reads, predictions, fits or a covariance claim.

[Shared receiver-law comparison](ilvis0-receiver-distance/README.md): all twelve saved-trajectory calculations completed. Full training cadence increases separation under both supplied receiver laws; the distances are not model votes or actual likelihood ratios.

[Accumulated IMU-noise sensitivity](ilvis0-joint-distance/README.md): all 24 fixed-trajectory comparisons completed. Independent added noise lowers noise-scaled separation with position differences unchanged. PSD values are software examples, not device measurements.

[Joint covariance projections](ilvis0-joint-projection-controls/README.md): both controls passed, including 64,080 epochs and twelve fixed training summaries in 52 seconds using about 88 MiB of accounted workspace. Inverse, transpose and projected covariance match an independent small reference; full aircraft uncertainty remains unqualified.

[Fixed-summary error certificates](ilvis0-summary-error-controls/README.md): all four declared noise cases pass in 36 seconds; twelve training summaries and 441 later coordinate errors share one simultaneous error budget. This qualifies supplied-law arithmetic, not actual instrument noise or complete aircraft prediction uncertainty.

[Saved native-summary binding](ilvis0-training-summary-controls/README.md): all six cases reproduce 180 original coordinate inequalities and independently audit 144 signed-summary inequalities, without new integration. This checks the five-epoch source binding; complete-cadence prediction remains open.

[Typed source-prefix copying](ilvis0-prefix-source-controls/README.md): all eighteen cases pass 1,188 tail-frame and 2,772 exact array comparisons against independent cold kernels. The [initial accounting rejection](ilvis0-prefix-source-controls-initial/README.md) is preserved. Source copying alone does not qualify complete native reuse.

[Complete native-prefix short controls](ilvis0-native-prefix-controls/README.md): twelve supported cases reproduce all original reports and 51 design columns; two broader sources retain the original rejection. Cached advancement uses 20 steps versus 34 cold steps per supported case. Long-history performance remains unqualified; the [initial missing-backend freeze](ilvis0-native-prefix-controls-initial/README.md) stays preserved.

[Initial long-record native-prefix comparison](ilvis0-native-prefix-long/README.md): four original references completed; two cases were not started. The bookkeeping failure and all charges are preserved. This did not qualify the batched method.

[Corrected long-record comparison](ilvis0-native-prefix-long-v2/README.md): all six cases completed. Eight retained report pairs match exactly, but tuple/list comparison failures and four missing later reports prevent qualification. All failures and twelve saved point checks are preserved.

[Missing cached-report recovery](ilvis0-native-prefix-format-recovery/README.md): all four batches pass, completing exact report and 51-column agreement for all six histories. No original calculation or point check was repeated. The [initial loader failure](ilvis0-native-prefix-format-recovery-initial/README.md) is preserved with zero charged work. Full-cadence prediction remains a separate gate.

[Independent prediction starting bounds](ilvis0-dense-physical-roots/README.md): all six generated cases pass at the first training epoch, retaining the full physical calibration range and excluding the old one-metre training proof. This establishes a supported starting calculation, not complete prediction qualification.

[Full-cadence training bounds](ilvis0-dense-physical-bounds/INTERPRETATION.md): all six cases stopped at the square-root-domain check; 348 partial reports are preserved and none qualified. Formal certification is a separate research track; the [revised prediction protocol](PREDICTION_VALIDATION.md) prioritizes training-only fitting and unused-position tests.

[Complete training/forecast controls](ilvis0-training-forecast-controls/README.md): all 24 forecasts closely reproduce the known paths, but only 3 fits pass the numerical stopping checks. The initial loader failure is preserved separately. No new aircraft fits have started.

[Prediction pilot selection](ilvis0-prediction-pilot-preparation/README.md): three stretches cover the available IMU/hemisphere cells without reusing a conservative flight group. Selection used metadata alone and preceded pipeline qualification and the separate fit freeze.

[Saved calibration-tangent audit](ilvis0-forecast-tangent-audit/README.md): six predeclared endpoints each retain only 12 distinguishable directions among 26 or 27 columns. Twelve saved-array linear solves show a minimum-norm correction improves some steps, but do not qualify a replacement solver.

[Near-zero stopping composition](ilvis0-training-forecast-controls/NEAR_ZERO_PLAN.md): 74 focused checks pass, including call accounting and 40 nonzero/boundary known-optimum cases. The separately frozen [matched comparison](ilvis0-near-zero-forecast-controls/README.md) now passes 24/24 cases using 2,976 native calls. Earlier failures remain preserved. The retrospective pilot proceeds through its own input/source/environment freeze.

[Initial prediction-pilot packaging failure](ilvis0-retrospective-prediction-pilot/README.md): all 72 setup identities stopped before any native calculation because a compiled source was omitted. Charges and inputs remain preserved; this allowance is closed.

[Completed three-recording prediction pilot](ilvis0-retrospective-prediction-pilot-v2/INTERPRETATION.md): all 72 fits return; 49 pass numerical checks. One northern recording completes all four matched settings, with 0.84–1.13 m later horizontal RMS for specified-field globe versus about 496 m and 793 m for the alternatives. The other two recordings retain numerical or accuracy failures. Saved-only reporting audits every error, cost, charge and accuracy label. This is retrospective development validation, not calibrated significance or independent confirmation.

[ESA geographic adapter qualification](esa-geographic-rate-controls/README.md): all 72 generated twenty-minute maneuvering cases pass. Linear point samples stay below 10 cm maximum position error; hold rules pass refinement but retain large absolute errors. The run used 144 native propagations in 31.29 minutes. Known initial state and zero antenna offset limit this qualification; actual sampling, calibration and receiver errors remain open. No ESA recording was read and no selection changed.

[ESA antenna and calibration controls](esa-observation-controls/README.md): all 24 generated cases pass in 10.61 minutes, using exactly 96 native calls. With supplied sensor and starting-state corrections and independently generated antenna positions, maximum spatial error stays below 10 cm. This checks application of corrections, not their recovery from observations. This study fitted only generated data.

[ESA training-only prediction controls](esa-training-forecast-controls/README.md): all 24 generated fits pass in 25.17 minutes, using 1,477 native calls. Initialization, weighting and fitting use earlier observations only; later positions are exposed after the forecast is saved. All nuisance columns and both error sections pass. These noiseless generated examples qualify the calculation, not instrument accuracy or statistical confidence. No observed or reserved flight was used.

[ESA receiver-error policy checks](esa-error-policy-checks/README.md): 21 policy checks and 55 covariance regressions pass. The versioned working cases retain full cross-axis covariance, common receiver-coordinate weights and explicit temporal correlation; dense and structured calculations agree. This is software verification, with no flight inventory or fit and no calibrated error claim.

[Prediction-input lineage checks](ilvis0-joint-projection-controls/NEXT_PLAN.md#keep-each-bound-tied-to-its-error-assumptions): twelve metadata cases preserve observations, source, parent constraints and the complete error allowance. Numerical integration with the dense-error interface remains pending; these are input checks, not prediction or coverage results.

[ESA full-motion development inventory](esa-development-selection-v2/README.md): after 154 source-bound software checks, one receiver-file pass admits two runs totaling 393.4 minutes. The 298.6- and 94.8-minute runs average 301.1 and 267.3 km/h. Turns and climbs are retained for explicit IMU motion reconstruction; no model fit or protected observation is used. The version-1 zero-eligible inventory remains unchanged.

[ESA pilot interval preparation](esa-development-pilot-preparation/README.md): 110 source-bound checks precede one complete pass through each original file. The first twenty-minute interval retains 360,029 raw IMU samples and 360,028 constructed intervals. Its 800 training and 400 later receiver positions are separate, both working error cases use earlier rows only, and a saved-data audit verifies all hashes, samples, support and charges. Preparation performed no model fit.

[ESA matched weighted training controls](esa-weighted-training-controls/README.md): all 48 generated cases pass after 113 source-bound software checks, using 490 native calculations in 5.01 minutes. The saved-data audit verifies both working receiver-error cases, every calibration column, independent Cartesian errors, unchanged raw inputs across starts and weights, and all charges. The largest later spatial error is below 0.08 mm in noiseless examples; that is a software result, not observed instrument precision. This qualified the separately frozen observed pilot.

[First observed ESA development pilot](esa-development-pilot/README.md): all 24 starts return; 15 pass numerical checks and nine model/settings forecasts are available. The sole complete three-model comparison has lower error for globe geometry, but its preferred forecast fails the accuracy limits. All eight field-globe forecasts miss later accuracy despite passing training accuracy. The run uses 1,524 native calculations in 2.32 hours; a saved-data audit verifies every error, label and charge. This is one development recording, not a successful independent replication. All original and protected sources remain untouched during fitting.

[Saved ESA prediction diagnosis](esa-development-diagnosis/README.md): completes after 13 source-bound checks, preserving nine usable forecasts and all three unavailable settings. Several calibration parameters reach bounds. The declared gravity reference varies by 0.00629 m/s², with an illustrative 187 m position scale; neither number establishes the actual error's cause. The run and audit use zero fits, propagations or original/protected reads. The [rejected setup](esa-development-diagnosis-setup/README.md) remains preserved separately.

[Gravity-mechanization controls](esa-gravity-controls/README.md): all 48 twenty-minute generated cases pass after 46 source-bound checks. Height-dependent gravity has at most 0.109 m spatial error at 300 Hz and 0.0273 m at 600 Hz. The run uses exactly 144 native calls in 17.17 minutes; saved-only reporting verifies all errors, derivative columns and charges. Initial state and calibration are supplied, so this qualifies neither their estimation nor an observed fit.

[Height-dependent training and forecasts](esa-height-training-controls/README.md): all 24 generated fits pass after 26 source-bound checks, retaining the original 0.1 m RMS /0.5 m maximum targets. The largest later error is below 0.02 mm in noiseless examples. The run uses 382 native calls in 39.08 minutes; saved-only auditing checks earlier-only anchors, independent physical errors, repeated input hashes and all charges. No original or protected recording is opened; these are software results, not instrument precision.

[Observed height-gravity revision](esa-observed-height-pilot/README.md): all 24 forecasts return after 33 source-bound adapter/reporting checks; eight fits pass numerical checks. Its one complete three-model setting favors globe and passes physical accuracy: later specified-field RMS is 6.80 m horizontal /13.71 m height, versus kilometre-scale alternatives. The same-start original forecast had 21.04/168.23 m RMS. All eight field-globe forecasts pass accuracy, but seven fail numerical cost stability. The run uses 1,478 native calls in 2.22 hours; saved-data reporting verifies every result and charge. One development recording does not establish independent confirmation or calibrated confidence.

[Stopping-check diagnosis](NUMERICAL_STOPPING.md): a shared saved-results checker passes seven metadata tests. It identifies nine position-stability failures in the original ESA pilot and seven additional cost-stability failures in the gravity revision. Frozen thresholds and saved hashes are verified, with no fitting, propagation or label changes.

[Fixed-point stopping resolution](esa-stopping-resolution/README.md): all 24 cases complete after 28 source-bound software checks, using 240 native sweeps in 21.90 minutes. Every baseline cost matches its saved value exactly, and repeated residuals and derivatives are identical. The original eight numerical passes, seven cost-stability failures and nine position-stability failures are reproduced. Field-globe local position changes stay below 4 micrometres; numerical precision is a next hypothesis, not an established cause. The saved-data report has four separately qualified source-binding checks. No fits, later observations, protected flights or original labels change.

[ESA scalar precision comparison](esa-precision-diagnostic/README.md): all 24 cases complete after 31 source-bound software checks, using 96 value calculations in 67.27 seconds. Both original residual vectors match exactly in binary64. Extended precision brings all eight field-globe cost changes below the existing limit, with a maximum of about 8.31×10⁻¹⁰; stable longitude wrapping alone is insufficient. Two source-bound presentation checks precede publication. No fitting or original fit labels change. The [initial zero-work setup failure](esa-precision-diagnostic-setup/README.md) is preserved separately; seven confirmation groups stay protected.

[Wider-precision long motion controls](esa-wide-tangent-controls/README.md): all 48 generated twenty-minute cases pass after 16 source-bound checks, using 144 native calls in 38.87 minutes. The original value calculation's largest errors are 0.109 m at 300 Hz and 0.0273 m at 600 Hz; the wider tangent agrees within 0.0000383 m in the reported coordinate-scaled comparison, retaining all 27 columns. A saved-only audit verifies every physical check and charge; all 580 publication artifact hashes are verified. No observed data or optimizer starts are used.

[Wider-precision training and forecasts](esa-wide-training-controls/README.md): all 24 generated cases qualify after 20 source-bound software checks, using 268 native calls in 113.96 minutes. The saved-only audit verifies all results, physical errors, source bindings and charges; all 466 publication artifact hashes are checked. The matrix preserves bounds, starts, stopping and accuracy targets. Later horizontal/height RMS stay below 9/4 micrometres in noiseless examples; these are software results, not instrument accuracy. Preparation copies are compacted into verified archives.

[Matched observed precision revision](esa-observed-wide-pilot/INTERPRETATION.md): completes 22 qualified forecasts after 56 source-bound checks, retaining all eight earlier passes and adding fourteen. Three of four matched settings favor globe plus the specified field and pass physical accuracy: later 3D RMS is about 15 m versus 3.8–4.4 km for zero-field globe and 7.4–8.6 km for disc. Two disc starts reach the eight-hour ceiling. All 412 publication artifact hashes are verified; 1,175 native calls and every failure are preserved. All settings reuse one development recording, with unchanged observations and physical assumptions. Confirmation groups remain untouched and statistical confidence remains uncalibrated.

[Saved prediction-error structure](esa-error-structure/INTERPRETATION.md): all 22 available curves and both deadline failures are preserved after 25 source-bound checks. The diagnostic processes 26,400 saved epochs in 3.15 seconds with no fits or propagation; all 88 publication artifact hashes are verified. Preferred-model later lag-one correlations are 0.991–0.992; first differences remain correlated at 0.974–0.981. This supports assessing combined receiver/IMU error assumptions before broader prediction tests, without changing model preferences or claiming calibrated confidence. Nonuniform query spacing leaves spectral checks unsupported rather than interpolated.

[Known-noise prediction test](esa-noisy-prediction/INTERPRETATION.md): all 24 fits pass numerical checks; none passes the unchanged physical accuracy screen. Later horizontal RMS is 83.6–88.6 m against a 10 m limit. All three generating candidates, both processing cases, both receiver policies and two starts are preserved. The test uses declared noise assumptions and no observed data. It finishes in 5.26 hours with 682 calls; the saved-only audit verifies all outcomes/charges and 477 publication artifact hashes. This blocks broader prediction fitting pending error-model qualification; it does not revise the original 53-stretch findings.

[Broader development-window plan](esa-broader-development/README.md): a metadata-only rule fixes first/last twenty-minute ranges in both eligible runs, preserving the already analyzed interval and selecting three additional candidates. Twelve source-bound checks pass; all nine planning artifact hashes and both sealed parent bindings are verified. All four ranges share one development group. No originals, decoding, numerical propagation or fitting are used; preparation and confirmation remain gated.

[Isolated arithmetic speed prototype](mixed-tangent-prototype/README.md): all nine source-bound checks pass after one released core becomes available. Six compiled cases retain bitwise-identical positions/residuals and all 26/27 derivative columns meet the fixed tolerance. The 84-source qualification reuses 78 parent-frozen dependencies and stores only six compressed source additions; all 12 publication artifact hashes are verified. The prototype reuses the shared loader without global patches. A long-record benchmark and fitting qualification remain required; no running method or scientific result changes.

[Long-record arithmetic benchmark](mixed-tangent-long-controls/README.md): all six generated twenty-minute cases preserve positions and residuals exactly, but none meets the fixed derivative tolerance. The prototype runs 4.7–5.6× faster in these native calls; it is not qualified for fitting. Twelve calls complete in 21.13 minutes on one thread. The saved-data audit verifies all cases and charges, and all 172 publication artifact hashes are checked. Existing methods remain unchanged.

[Selective-precision long-record benchmark](mixed-tangent-hybrid/long-study/README.md): all six frozen generated twenty-minute cases pass the unchanged derivative, position, residual and timing-boundary checks. Twelve native calls and six construction journals verify; the native-call CPU speedup is 2.03–2.21× against the wide reference. The publication archives 348 selected paths, all verified by hash. No observed inputs or optimizer starts were used.

[Selective-precision paired fitting and prediction](mixed-tangent-hybrid/paired-qualification/README.md): all six generated two-minute pairs pass independent convergence and physical prediction checks. Across 714 forecast positions, the largest three-dimensional difference from the unchanged wide reference is 1.40 × 10⁻⁹ m. The sealed result inspection verifies all six cases and 120 charged native calls; publication retains the frozen plan, source and input evidence. No observed data were used and no Earth-model decision was made.

[Twenty-minute paired fitting](mixed-tangent-hybrid/long-fit-study/README.md): all six generated cases pass independent convergence, physical prediction and matched wide/selective comparison. Across 7,194 forecast positions, the largest difference is 1.63 × 10⁻⁹ m. The sealed audit verifies 136 charged native calls and no errors. The first release's pre-charge adapter failure remains preserved. Timing was measured in a subsequent separate study; no observed recording or protected confirmation group was used.

[Whole-fit CPU timing](mixed-tangent-hybrid/timed-fit-study/README.md): all six generated twenty-minute pairs pass again. After compilation, selective fitting uses 1.96–2.61 times less CPU by case, with a 2.38 median wide/selective ratio; the frozen operational speed criterion passes. The sealed audit verifies 136 charged native calls and 340 publication artifact hashes. This measures software performance, not an Earth-model preference. An observed-data source-bound release remains before replacement.

[ESA same-source tangent comparison](esa-observed-hybrid/combined/README.md): the original study and its finite continuation are closed. A 17-test source-bound audit verifies the full 24-case ledger and every charged attempt. Twenty-one pairs pass; two lack qualifying matched fits, one exceeds the fixed 0.01 m forecast-difference limit at 0.016715 m, and training-cost primary starts agree in only 7 of 10 complete groups. A [saved-only check](esa-observed-hybrid/PRIMARY_DIAGNOSTIC.md) finds the start flips change forecasts by at most 0.000079 m. A [second saved-fit check](esa-observed-hybrid/FAILURE_DIAGNOSTIC.md) records parameter and forecast differences for each failed pair without refitting. The faster method is not qualified for general use. Four original technical interruptions remain recorded; the earlier wide pilot is historical because its fitting source differs. Seven ESA confirmation groups remain protected.

[ESA same-point derivative check](esa-observed-hybrid/same-point-result/README.md): the first allowance ended with three direct-loader errors and zero native calls. A separately frozen corrected allowance completed three tasks and all twelve charged calls. Independent replay confirms identical position values and boundary counts at both saved points in each failed pair; the largest derivative difference is about 0.0000012 m per normalized parameter unit. This is a numerical diagnostic, not a new fit or a qualification of the faster method. No protected ESA group was read.

The [revised selective tangent](mixed-tangent-hybrid/README.md) widens the two
attitude directions with the largest saved derivative differences. Source
generation and six short generated physical checks pass. A separate
[six-point ESA check](esa-observed-hybrid/same-point-v2/README.md) verifies
all six predeclared improvement gates with six charged native calls, no new
fits and no protected reads. Observed-fit substitution remains unqualified;
the wide method stays in use. The separately frozen
[three-pair development run](esa-observed-hybrid/three-pair-v2/WALL_CAP.md)
sealed three wall-cap failures after 349 charged native calls. Each preserved
its wide fit and forecast; two wide fits passed numerical stopping and one did
not. No revised fit or paired comparison completed.
The five-check interruption recovery route applies only to unfinished tasks;
these budget failures are complete and remain unchanged. Substitution is still
unqualified.

A [model-declared tangent audit](mixed-tangent-hybrid/MODEL_DISPATCH_RESULT.md)
reuses the sealed 24-case comparison: the first selective method passes all
16 globe pairs, while the flat candidate retains all eight wide outcomes,
including one numerical failure. All 24 selected numerical dispositions
match the wide reference. Eight focused tests pass, including generated kernel
comparisons for all three models and both processing settings. Two short
generated smoke cases reach the complete fit/forecast path with matching
inputs and forecasts, but their eight-evaluation fits do not converge. The
dispatch had no observed fit or speed qualification at that stage. The wide
method remained in use during the later observed check, which is reported below.

The [model-declared generated fit study](mixed-tangent-hybrid/dispatched-fit-study/README.md)
then passed all six two-minute physical-model/processing pairs. Its sealed
replay verifies the source, charges, model choices and matched forecasts;
the largest position difference from wide precision is 1.40 × 10⁻⁹ m.
It charged 120 native calls with no errors. This qualifies the tested
generated software path, while observed-aircraft substitution remains open.

The [observed model-declared check](mixed-tangent-hybrid/OBSERVED_DISPATCH_PLAN.md)
used sixteen globe cases from ESA development recording 187. Its first launch
preserved sixteen technical failures at zero native calls. The
[corrected release](esa-observed-model-dispatch-v2/README.md) passed 92
source-bound software checks plus five reboot-recovery checks and sealed
16/16 fits under 1,240 native calls. Its saved-only audit verified all
16 forecast pairs against the 0.01 m rule and retained the earlier flat
numerical failure. Only 5/8 training-selected primary starts agree, so the
faster method **did not qualify** for observed-data replacement. The three
start switches are near ties, with saved cross-primary forecasts differing
by at most 0.00007914 m; the [cost audit](mixed-tangent-hybrid/START_TIE_AUDIT.md)
and [method diagnostic](mixed-tangent-hybrid/README.md)
does not alter the frozen gate. No Earth-model preference or observed error-law
qualification follows from this method study. The
[sealed runtime record](esa-observed-model-dispatch-runtime/README.md) remains
readable from verified archive packs after compaction. A separate
[portable evidence copy](ESA_DISPATCH_PORTABLE.md) verifies all 576 archived
artifacts without the shared pack catalog.

The [two-start generated study](mixed-tangent-hybrid/START_EQUIVALENCE_RESULT.md)
froze a truth-free start-equivalence rule and completed all 12 paired tasks
under 240 native calls. Every task passed its individual checks, but only
the two flat settings passed the full six-setting rule. The four globe
settings failed the predeclared relative training-cost tolerance; one also
selected a different primary start. Selected forecasts nevertheless agreed
within 1.75 × 10⁻⁹ m. The [verified study record](mixed-tangent-hybrid/start-equivalence-study/README.md)
retains the source, qualification, charges and failures. This failed gate
does not revise the observed exact-start result or authorize substitution
in an aircraft fit.
A separate [revised-rule diagnostic](mixed-tangent-hybrid/START_EQUIVALENCE_V2_METHOD.md)
passes all six settings when applied to those already sealed outputs, using
the pre-existing near-zero solver cost ceiling and an explicit within-method
forecast check. It is retrospective; the original 2/6 qualification remains
failed, and new generated and observed checks are still required.
The [fresh 180-second generated study](mixed-tangent-hybrid/START_EQUIVALENCE_V2_RESULT.md)
subsequently sealed 12/12 passing tasks and passed all six revised-rule
settings. Its largest across- or within-method forecast difference was
3.13 × 10⁻⁹ m. It qualifies this generated method gate only; the failed
original study stays failed and observed-aircraft substitution remains gated.
A [retrospective ESA start audit](mixed-tangent-hybrid/OBSERVED_START_V2_RETROSPECTIVE.md)
then passed the revised rule in all eight saved observed groups using the
previously declared relative cost tolerance and no absolute floor. The
largest near-tied forecast spread was 0.00407 m. It made no new fit; the
original exact-start failure remains and prospective observed qualification
is still required.

The [fresh ESA solver comparison](mixed-tangent-hybrid/OBSERVED_DISPATCH_FRESH_RESULT.md)
passed all 16 pairs on one 20-minute development window. The
[saved trial-work audit](mixed-tangent-hybrid/OBSERVED_TRIAL_WORK_RESULT.md)
found that a value-only proposal check could avoid derivative calls in
one of the 16 pairs. It checked all 32 fit records without rerunning them.

[Withheld ESA forecast accuracy](mixed-tangent-hybrid/ESA_DISPATCH_ACCURACY_RESULT.md)
scored all 32 paths against 400 later positions from the same window, with no
new fits. Four of 16 primary paths met the full-horizon limits. Those paths
used the specified field and the persistent receiver error policy.

The [cohort work check](FLIGHT_GROUP_DECISION.md#when-the-whole-cohort-can-stop)
uses sealed targets to check whether unfinished reference draws could change
either final decision. Its possible outcomes agree with exhaustive controls.
No aircraft data or reference calculations were added.

The [ESA group evidence index](analysis-provenance/ESA_GROUP_EVIDENCE.md)
binds the principal forecast cuts to their original receiver rows. Fourteen
scored cuts reuse one development group. Seven groups remain reserved.

The [ESA forecast timing check](prediction-observed-development/ESA_FORECAST_TIME_SHIFT_RESULT.md)
scores eight original paths after a constant shift learned from the other
windows. It slightly worsened the combined omitted score and left the same
one window within the working reference. All eight tasks completed without
new fits or access to reserved flights.

[ESA forecast-error persistence](prediction-observed-development/ESA_INNOVATION_PERSISTENCE_RESULT.md)
improves the omitted log score in all eight windows while keeping their fixed
variances and forecasts. Two meet the error reference. All eight tasks closed.

[Joint variance and persistence](prediction-observed-development/ESA_JOINT_PERSISTENCE_RESULT.md)
improves every omitted log score and puts six of eight windows inside the
unchanged reference. All sixteen starts reach the evaluation cap and their
best scored donor points are retained. No new trajectory fits were run.

[ESA error-fit stopping audit](prediction-observed-development/ESA_JOINT_PERSISTENCE_STOPPING_RESULT.md)
reproduces all eight saved donor scores and finds a feasible downhill direction
in each. All original evaluation-limit outcomes stand. No new fit was run.

[ESA error-fit refinement](prediction-observed-development/ESA_JOINT_PERSISTENCE_ANALYTIC_RESULT.md)
passes all eight donor stopping checks with the verified derivatives. Both
input conventions retain the same six of eight windows inside the reference.

[ESA forecast error by report](prediction-observed-development/ESA_PERSISTENCE_WINDOW_DIAGNOSTIC_RESULT.md)
reproduces all 16 joint scores and locates the two misses in time and across
axes. It uses fixed settings, with zero new fits or reserved-flight reads.

[ESA training-motion replay](prediction-observed-development/ESA_PERSISTENCE_HISTORY_RESULT.md)
tests the effect of earlier maneuvers under the same decay and fitted error
settings. Both input conventions still place the same six windows inside
the reference.

[ESA window-scale mixture](prediction-observed-development/ESA_WINDOW_SCALE_MIXTURE_RESULT.md)
improves the omitted log score by 9.10 units under both input conventions.
Seven of eight windows fall inside its reference. The high-error steady
window remains outside.

[ESA forecast receiver substitution](prediction-observed-development/ESA_FORECAST_RECEIVER_TRANSFER_RESULT.md)
scores the same eight windows against three GPS solutions. The count
inside the reference varies from seven to three to two even with
centimetre-scale receiver differences.

[ESA receiver difference covariance](prediction-observed-development/ESA_RECEIVER_CONTRAST_COVARIANCE_RESULT.md)
compares models on those measured differences. Separate receiver terms
improve the summed omitted score by 70.83 units over an unrestricted
covariance. Slow errors shared by the receivers remain unresolved.

[ESA receiver covariance replacement](prediction-observed-development/ESA_RECEIVER_COVARIANCE_COMPATIBILITY_RESULT.md)
finds that the separate receiver term cannot be removed in full from the
existing forecast covariance. All 16 compatibility checks fail.

[ESA combined forecast and receiver covariance](prediction-observed-development/ESA_ADDITIVE_RECEIVER_COVARIANCE_RESULT.md)
improves the overall prediction score. The model assigns too much
uncertainty to six of eight windows scored with the original GPS solution.

[ESA raw carrier and GPS position comparison](prediction-observed-development/ESA_RAW_PHASE_PPP_CLOSURE_RESULT.md)
checks all three same-antenna pairs on a separate interval. Projected
one-second changes only partly explain the relative carrier readings.

[ESA receiver agreement over longer blocks](prediction-observed-development/ESA_RAW_PHASE_PPP_TIMESCALE_RESULT.md)
sums those same carrier and position contrasts over 4, 16 and 60
seconds. Agreement does not improve consistently.

[ESA chronological GPS comparison](prediction-observed-development/ESA_PPP_COVARIANCE_CHRONOLOGY_RESULT.md)
learns relative receiver error from the first 97 of 195 windows. Faster
changes transfer to the later 98. Late offsets are much larger than expected.

[ESA conditional GPS offset forecast](prediction-observed-development/ESA_PPP_OFFSET_FORECAST_RESULT.md)
uses earlier relative offsets to predict later ones. At a one-window
lead, RMS falls from 39 mm to 6 mm, but the uncertainty remains too small.

[Same-realization noise attribution](noisy-realization-attribution/INTERPRETATION.md): the first six-task run closed with six sealed software-path failures before any native forecast. A test reproduced the project-root error, and the corrected source passed 16 bound checks. The separate six-task study completed with six technical passes and six native calls, but zero forecasts meet physical accuracy: known-calibration horizontal error is 439–508 m, versus 84–89 m in the earlier fitted forecasts. A [full-length clean control](noisy-realization-attribution/long-noiseless-control/README.md) passes at 0.048 m later horizontal RMS. A separate [one-task conditioning comparison](noisy-realization-attribution/conditioning-comparison/README.md) passes and audits all 361,200 charged native steps: its expected later horizontal scale is 717.66 m unconditioned and 33.77 m after using 800 earlier receiver observations. The [ten-variant component replay](noisy-realization-attribution/component-decomposition/README.md) passes all ten tasks and matches the sealed full-noise oracle exactly. In the preselected generated case, isolated changing gyro bias gives 376 m later horizontal RMS and gyro white increments 230 m, versus 20 m and 6 m for the accelerometer components. No new aircraft data were used; historical failures remain unchanged.

[Earlier ESA logged-rate variation](esa-training-rate-variation/README.md): 21 source-bound checks qualify the diagnostic. It examines 239,864 saved training samples over 13.33 minutes and 109,536 fixed three-point contrasts in 2.36 seconds. Variation changes markedly with sample spacing. No fits, native calculations or original/protected reads occur; aircraft motion, filtering and noise remain separate possible contributors. This does not calibrate an error law or revise the running noise test.

[Accumulated-noise covariance software](integrated-noise-covariance/README.md): 32 source-bound checks pass, including the initial 26 and six conditional-forecast cases. Independent dense calculations agree for all 27 columns and for future means and marginal covariance at four training cutoffs. A constant-level example matches analytic covariance; the long case uses 64,080 generated epochs and 59.2 MiB of stored arrays. Both source snapshots remain verified; the extension adds three archive objects and twelve verified publication artifacts. Aircraft error-law calibration and fitted-parameter uncertainty remain open.

The [changing-bias extension](integrated-noise-covariance/OU_PLAN.md) brings that component to 46 source-bound checks. Its thirteen-state example agrees with independent double integrals and separately implemented OU endpoint/integral moments, including the declared stress scales. Fifteen publication artifact hashes are verified; twelve source snapshots add four archive objects. This remains a constant-level software example, with no aircraft fits or calibrated archive error law.

[Native single-step noise linearization](native-noise-linearization/README.md): all 18 source-bound checks pass across twelve physical-candidate/processing/gravity combinations. Extended mean observations match the existing wider calculation; all fifteen state/input directions match finite differences and 21 calibration chains agree with the reference. The journal verifies 489 one-packet calls and two builds. All 38 publication artifact hashes, including compiled sources/binaries, are checked. Twenty-nine source snapshots add five archive objects. Complete-history propagation and fitted-calibration uncertainty remain open.

[Shared query/endpoint noise](integrated-noise-covariance/JOINT_PLAN.md): the covariance component now passes 54 source-bound checks, retaining the earlier 46. Explicit shared-noise and legacy modes match independent dense whitening and earlier-only conditioning, including a partial-packet example. Seventeen publication artifact hashes are verified; fourteen source snapshots add three archive objects. No native calls or flight fits occur. Complete native-history composition remains the next gate.

[Persistent receiver errors](integrated-noise-covariance/RECEIVER_PLAN.md): all 15 source-bound checks pass. The extension preserves native shared drivers while adding receiver offsets, drift and up to two correlated components with per-epoch cross-axis transformations. Independent dense covariance, all 27 design columns and earlier-only prediction agree. The largest checked state has 27 coordinates. All 24 publication artifact hashes are verified; 21 archived source snapshots add four objects. No native calls, flight fits or original/protected reads occur. Fitted-calibration uncertainty remains open.

[Complete native-noise histories](native-noise-linearization/README.md): all 38 source-bound checks pass. Twelve 600-packet cases preserve the original wider nominal positions; short-history covariance agrees with independent nonlinear perturbations along 54 driver directions, with normalized discrepancy below one part per million. The run uses 20,392 native calls, 27,580 packet steps and two builds in 9.51 minutes. All 59 publication artifact hashes and the complete charge chain are verified. Fifty source snapshots add four archive objects. Calibration remains fixed; original/protected reads and flight fits are zero.

[Combined native and receiver errors](native-noise-linearization/COMBINED_PLAN.md): all twelve cases pass across the candidate, processing and gravity combinations. The 27-state calculation preserves native means, matches independently summed covariance and whitens every active calibration column; earlier-only future moments match dense conditioning. All 64 artifact hashes and 108 native calls, 144 packet steps and two builds are verified. Fifty-five source snapshots add two archive objects. No original/protected reads or flight fits occur; calibration is fixed.

[Calibration uncertainty in linear prediction](integrated-noise-covariance/CALIBRATION_PLAN.md): all 15 checks pass, including 27-column cases, redundant parameters, unidentifiable forecasts and parameter-unit changes. Earlier-only predictions and their covariance agree with independent dense GLS prediction weights. Unknown calibration directions are retained; forecasts they can change receive no finite covariance. All 23 artifact hashes are verified; twenty source snapshots add three archive objects. This checks an unrestricted linear mean, not nonlinear calibration or active parameter bounds. No native calls, flight fits or original/protected reads occur.

[ESA rate-point error law](integrated-noise-covariance/POINT_PLAN.md): all 15 checks pass against independent dense point-error covariance and trapezoidal integration. Adjacent intervals preserve their common sample, including unequal intervals, cross-axis covariance and zero/singular components. The law distinguishes per-sample variance from continuous PSD and sampled bias from a continuous OU integral. All 23 artifact hashes are verified; twenty source snapshots add three archive objects. No native calls, fitting or original/protected reads occur. This qualified the separately checked native adapter below.

[Source-specific native error propagation](native-noise-linearization/README.md): all 180 source-bound checks pass, including 65 native adapter checks. Twenty-four longer cases preserve nominal positions for both input laws; twenty-four short cases agree with independent nonlinear perturbations, with maximum normalized covariance discrepancy about 1.1 parts per million. Two full receiver cases retain 33 states; twelve earlier incremental combinations remain passing. The run uses 23,984 calls, 39,594 packet steps and two builds in 36.3 seconds. All 77 artifact hashes, 63 prepaid identities and their actual attempts are verified. Sixty-seven archived source snapshots add ten objects. Sixteen accounting controls check interruption, overspend and no retries. No fitting or original/protected reads occurs; native calibration and nonlinear coverage remain open.

The [portable qualification revision](native-noise-linearization/point-native-ci-qualification/evidence-receipt.json) passes 182 checks, adding two controls that separate routine tests from formal qualification. Ordinary generated tests need no local report files; formal runs still require exact source/environment bindings. Only the test harness changes. The same 23,984 calls and 39,594 packet steps finish in 35.5 seconds; all 77 artifact hashes and 63 prepaid identities are verified. One additional source object preserves the revision. The earlier 180-check evidence remains unchanged.
## Linked calibration bounds

[ESA calibrated-box derivative signs](prediction-observed-development/ESA_LINKED_MONOTONE_RESULT.md)
checks 165 archived directions. No derivative has a verified fixed sign
over its box, so the previous upper bounds stay in place.

[ESA calibration-resistant contrast](prediction-observed-development/ESA_CALIBRATION_ORTHOGONAL_RESULT.md)
leaves a positive gap in the saved affine calculation, with only
0.48 micrometres of nonlinear position error allowed per coordinate.

[ESA maximum-margin contrast](prediction-observed-development/ESA_CALIBRATION_MAXIMUM_MARGIN_RESULT.md)
brackets the best affine allowance at 12.18 cm when the contrast
can use earlier coordinates freely.

[ESA forecast-conditioned margin](prediction-observed-development/ESA_CALIBRATION_CONDITIONED_MARGIN_RESULT.md)
certifies a 0.86 µm allowance when the earlier positions enter through
the covariance forecast. The search exhausts its iteration allowance,
leaving 12.18 cm as the upper bound.

[ESA compact forecast margin](prediction-observed-development/ESA_COMPACT_FORECAST_MARGIN_RESULT.md)
solves the same conditioned affine problem through the state at the
forecast cut. The best allowance is 2.25 cm, below the earlier
4.03 cm integration reference.

[ESA integrated contrast support](prediction-observed-development/ESA_INTEGRATED_CONTRAST_SUPPORT_RESULT.md)
shows how coordinate errors accumulate in the same score. The
contrast allows 4.69 mm/s if velocity errors act alone, with nearly
all the sensitivity after the forecast cut.

[ESA contrast replay](prediction-observed-development/ESA_CONTRAST_REPLAY_RESULT.md)
reproduces four earlier calibration examples with full integration.
Model separation changes by less than 0.073% of the certified affine
gap at each point.

[ESA earlier-loss support](prediction-observed-development/ESA_CONTRAST_TRAINING_SUPPORT_RESULT.md)
excludes both points behind the box-only upper bound, with the lower
allowance still at 2.25 cm.

[ESA score-aligned earlier GPS](prediction-observed-development/ESA_CONTRAST_SCORE_ALIGNED_RESULT.md)
checks six directions chosen for their effect on the forecast score.
The 2.25 cm lower allowance stays unchanged.

[ESA fixed-receiver overlap](prediction-observed-development/ESA_FIXED_REFERENCE_WINDOW_RESULT.md)
verifies 61 Reykjavík station times within the aircraft's second
preselected stop. Its station is 0.93 km away and the original data
and exact excerpt are recorded.

[ESA matched raw GPS](prediction-observed-development/ESA_FIXED_REFERENCE_PAIR_RESULT.md)
matches all 61 station times in the original aircraft log. Both
receivers track ten common satellites continuously across the stop.

[ESA Reykjavík relative phase](prediction-observed-development/ESA_FIXED_REFERENCE_PHASE_RESULT.md)
finds disagreement with the original aircraft path, reaching 0.85 m
vertical RMS. Neither solution supplies a qualified ground reference
for the aircraft uncertainty model.

[ESA Reykjavík carrier bands](prediction-observed-development/ESA_FIXED_REFERENCE_BAND_RESULT.md)
shows that both bands reproduce the disagreement, giving paths that
agree with each other to about a centimetre per axis.

[ESA Reykjavík clock replay](prediction-observed-development/ESA_FIXED_REFERENCE_CLOCK_RESULT.md)
applies the recorded receiver clock offsets to times, code and carrier
phase. The vertical difference from the aircraft GPS path remains
0.85 m RMS.

[ESA Reykjavík direct Doppler](prediction-observed-development/ESA_FIXED_REFERENCE_DOPPLER_RESULT.md)
sealed 3,601 aircraft and 61 station velocity estimates. The integrated
aircraft path differs from both position paths by about 15 m vertically
RMS and cannot resolve their sub-metre difference.

[ESA in-flight Doppler and shape score](prediction-observed-development/ESA_DOPPLER_CONTRAST_RESULT.md)
integrates the two saved satellite velocity paths continuously through
the training cut. They shift the frozen shape score by 31.5% and 25.8%
of its certified gap on one development interval.

[ESA shared-motion check](prediction-observed-development/ESA_SHARED_MOTION_GAP_RESULT.md)
constructs the minimum acceleration-energy error that shifts the fixed
score by its certified gap while closing exactly in position and velocity
at both ends of the later window.

[ESA carrier signature of shared motion](prediction-observed-development/ESA_SHARED_MOTION_CARRIER_RESULT.md)
finds that the archived satellite clock change does not match the
correction needed to hide the constructed displacement. The common-set
comparison gives 0.58 mm clock change and 4.88 mm required change RMS.

[Nuuk Museum reference search](prediction-observed-development/ESA_GROUND_REFERENCE_AVAILABILITY.md)
verifies an EarthScope listing for a 1 Hz ground receiver on the Greenland
flight date. The file requires sign-in before coverage can be checked.

[Carrier signature at the Nuuk receiver's cadence](prediction-observed-development/ESA_NKAR_CADENCE_RESULT.md)
sums 240 saved aircraft differences into 120 one-second pairs. The
constructed motion retains a 9.77 mm RMS range signature. The archived
satellite clock update accounts for little of that pattern.

[Permanent Nuuk receiver overlap](prediction-observed-development/ESA_NUUK_GROUND_INTAKE_RESULT.md)
matches 17 times at 30-second spacing. The four times within the
two-minute test share 11 continuous dual-frequency satellite arcs.

[Permanent Nuuk carrier comparison](prediction-observed-development/ESA_NUUK_GROUND_PHASE_RESULT.md)
finds 3.55 cm RMS differential range error on the saved aircraft path,
rising to 18.90 cm when the constructed displacement is added. The result
covers three 30-second differences on the development flight.

[Between-sample motion at Nuuk](prediction-observed-development/ESA_NUUK_BETWEEN_SAMPLES_RESULT.md)
finds an exact error path that spans the score gap and vanishes at all four
ground observations. The minimum RMS acceleration is 1.876 mm/s², 14%
above the earlier example.

[Between-sample motion against the aircraft carrier data](prediction-observed-development/ESA_NUUK_BETWEEN_CARRIER_RESULT.md)
raises the saved aircraft path's residual from 3.77 to 4.74 mm RMS.
The archived satellite clock change explains little of the range error
that would hide the displacement.

[Final satellite orbit and clock check](prediction-observed-development/ESA_NUUK_ORBIT_CLOCK_RESULT.md)
adds the final orbit positions on identical satellite support. About 3.07 mm RMS
of the required signed correction remains. The check used the open development
flight and required no new fits.

[Carrier error needed to change the score](prediction-observed-development/ESA_CARRIER_SCORE_BOUND_RESULT.md)
extends the one-displacement replay to all directions in the linearized range
model. Under its anchor and motion limits, the full score gap requires at least
1.97 mm RMS of structured range error. Actual aircraft error remains open.

[Position accuracy needed at the anchors](prediction-observed-development/ESA_CARRIER_ANCHOR_ERROR_RESULT.md)
allows errors at the four Nuuk times and both endpoints. With a hypothetical
1 mm RMS carrier-error cap, about 1 m per position coordinate is allowable.
The calculation specifies what an independent reference would need to establish.

[Ground sampling and the carrier score](prediction-observed-development/ESA_CARRIER_SCORE_CADENCE_RESULT.md)
finds that the actual 30-second totals cannot directly see the carrier pattern
between their endpoints. Ideal one-second coverage could see nearly all of it.

[Ground cadence and score sensitivity](prediction-observed-development/ESA_GROUND_GRID_SCORE_RESULT.md)
compares the verified permanent Nuuk times with ideal one-second anchors.
The complete grid makes between-sample errors much less influential. Its
position-only threshold is 4.65 cm per coordinate for the tested score.

[High-rate ground file intake](prediction-observed-development/ESA_NKAR_INTAKE_READY.md)
passes 17 software checks and reproduces the original-to-expanded hashes
and 2,880 epochs of a public legacy RINEX day. Actual Nuuk Museum coverage
remains to be checked.

[One-second matched ground score](prediction-observed-development/ESA_NKAR_GROUND_SCORE_PLAN.md)
passes eleven software checks. The real comparison awaits the Nuuk Museum
station day and will preserve missing intervals and unresolved error directions.

[Reserved ESA receiver coverage](external-imu-data/ESA_CONFIRMATION_RECEIVER_INVENTORY_RESULT.md)
finds ten provisional windows across all seven reserved flight groups.
The screen uses GPS coverage and quality. IMU timing, model fits and
prediction validation are separate steps.

[Reserved ESA timestamp integrity](external-imu-data/ESA_CONFIRMATION_TIMING_RESULT.md)
verifies a 20-minute slice in each group. All seven slices have complete
timestamp coverage and no gaps larger than 5 ms. Sensor-value columns
were left unread.

[Public Qaqortoq ground intake](prediction-observed-development/ESA_QAQ_GROUND_INTAKE_RESULT.md)
matches all 121 seconds of the development window at a distance of 456–458 km.
The distant receiver can check some shared satellite errors.

[Qaqortoq one-second range comparison](prediction-observed-development/ESA_QAQ_GROUND_SCORE_RESULT.md)
uses all 120 intervals. They expose 98% of the carrier weight norm, and the
matched aircraft-minus-ground discrepancy is equivalent to 2.46% of the score
gap. The comparison leaves absolute accuracy open.

[Does a Qaqortoq correction help later?](prediction-observed-development/ESA_QAQ_PHASE_TRANSFER_RESULT.md)
uses 335 earlier and 120 later one-second intervals. The earlier correction
lowers later range RMS by 0.38% and moves the score by 0.31% of its gap.

[Ground receivers at the same cadence](prediction-observed-development/ESA_GROUND_CADENCE_COMPARISON_RESULT.md)
finds that corrections from both stations help over the same three later
30-second intervals. The archived products and aircraft paths differ. The
result leaves faster shared error open.

[Shared satellite products and aircraft path](prediction-observed-development/ESA_GROUND_COMMON_PRODUCTS_RESULT.md)
reduce the later range difference between Nuuk and Qaqortoq from 3.48 to
1.47 cm RMS. Both corrections improve agreement with the same saved path.

[Joint carrier and position error budget](prediction-observed-development/ESA_REFERENCE_ERROR_BUDGET.md)
combines five saved reports. It shows why the small summed residual does not
bound aircraft error and gives the measurement requirements for the fixed gap.

[Geometric carrier approximation](prediction-observed-development/ESA_CARRIER_RANGE_REMAINDER_RESULT.md)
checks every final satellite endpoint and bounds the score error from using
linear ranges. Under the illustrative position and motion limits it is at most
0.27% of the gap.

[Ground phase correction across time](prediction-observed-development/ESA_NUUK_PHASE_TRANSFER_RESULT.md)
uses earlier permanent Nuuk observations to lower the later aircraft range
residual from 4.38 to 1.92 cm RMS across three unused intervals.

[Position effect of the ground phase correction](prediction-observed-development/ESA_NUUK_PHASE_POSITION_RESULT.md)
projects later range residuals through the saved satellite geometry.
The peak accumulated height adjustment falls from 21.62 to 5.19 cm.

[Curvature-guided solver retry](prediction-group-transfer/CURVATURE_RETRY_CONTROLS_RESULT.md)
compares the same eight generated cases with and without shorter
curvature-informed steps. Both versions pass four cases. The
qualification failed, and the aircraft fits remain unchanged.

[Residual curvature controls](prediction-group-transfer/RESIDUAL_CURVATURE_CONTROLS_RESULT.md)
pass five of eight generated cases with either analytic or
finite-difference curvature. The exact audit recovers small positive
cost gaps on three failed starts whose reported costs equal the optimum.

[Direct residual change controls](prediction-group-transfer/DIRECT_RESIDUAL_CHANGE_RESULT.md)
pass six of eight cases with either curvature method. They recover
the curved-interior start by estimating its small trial improvement
accurately. Both weak-direction starts still fail.

[Strong-residual correction](prediction-group-transfer/STRONG_RESIDUAL_RESTORE_RESULT.md)
passes all eight generated starts with analytic curvature. The
finite-difference arm gives smaller weak-direction errors and still
passes six. The observed solver stays unchanged.

[Weak-direction tangent curvature](prediction-group-transfer/WEAK_TANGENT_CURVATURE_RESULT.md)
passes all eight generated controls with estimated curvature under
the unchanged evaluation allowance and fresh convergence gate.
Flight-scale qualification remains open.

[Weak curvature on a generated flight](prediction-group-transfer/WEAK_CURVATURE_FLIGHT_RESULT.md)
reaches the fixed wall limit after 181 attempted training tangents and
saves no forecast. The sealed trust-region reference passes in ten
evaluations. The flight-scale qualification failed.

[Trial-tangent curvature controls](prediction-group-transfer/TANGENT_SECANT_CURVATURE_RESULT.md)
pass eight of eight in 80 evaluations, with no separate derivative probes.
Native forecast qualification follows its own matched protocol.

[Trial-tangent curvature on a generated flight](prediction-group-transfer/TANGENT_SECANT_FLIGHT_RESULT.md)
passes the first matched forecast with 49 training tangents. The
withheld position paths differ by at most 3.56 micrometres.

[Trial-tangent checks on the other two geometries](prediction-group-transfer/TANGENT_SECANT_GEOMETRY_RESULT.md)
closed all four fits. The disc pair passed with 63 candidate evaluations
versus 77 for the reference. The zero-field globe candidate stopped short of
convergence and failed the matched comparison.

[Bounded fallback on three generated flights](prediction-group-transfer/TANGENT_SECANT_FALLBACK_RESULT.md)
preserved the specified-field globe and disc passes. The zero-field globe
reached its time limit after 134 training attempts and saved no forecast.
