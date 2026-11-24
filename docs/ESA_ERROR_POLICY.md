# Working assumptions for ESA receiver errors

The next test needs an aircraft error model that covers GPS errors shared
across receivers, inertial sensor errors, and uncertain fitted corrections.
On the development flight, ground references help constrain some shared
GPS effects. Faster errors and airborne antenna effects remain open.
[Ground evidence](prediction-observed-development/ESA_GROUND_REFERENCE_EVIDENCE.md) ·
[Accuracy requirements](prediction-observed-development/ESA_NKAR_ERROR_BUDGET_RESULT.md) ·
[Confirmation plan](NEXT_STEPS.md)

The [two-band carrier replay](prediction-observed-development/ESA_CARRIER_BAND_RESULT.md)
found weak agreement between the aircraft and distant Qaqortoq corrections.
It measures the change already applied in the dual-frequency carrier
reconstruction. Errors that remain in that reconstruction still need a
separate bound.

The receiver export reports uncertainty in north, east and height, including
the correlations between those axes. These values help weight a fit; they are
not an independent measurement of the receiver's true error.

The completed position assessment found residual correlation after fitting
local trends. That supports testing persistent errors, but does not determine
their exact size or duration. The following two cases are fixed research
assumptions. Neither provides calibrated confidence or a detection threshold.

| Case | Added uncertainty floor, north/east/height | Scale of standard deviations | Correlated variance share | Correlation time |
|---|---|---:|---:|---:|
| Short memory | 0.05 / 0.05 / 0.15 m | 1 | 95% | 1 second |
| Larger persistent errors | Same floor, before scaling | 3 | 95% | 60 seconds |

The floor is added in quadrature to the reported covariance. Scaling applies
to the full matrix, preserving its cross-axis terms. Five percent of the
working variance remains independent between observations. The rest follows
the stated exponentially decaying correlation.
The time-varying loading uses each working matrix's lower Cholesky factor,
followed by the common receiver-coordinate conversion. This fixes the
cross-time interpretation as well as the within-epoch variances.

The numbers above are chosen sensitivity cases, not sensor specifications,
estimated error bars or guaranteed bounds. They are set before examining any
ESA model preference. A common preferred geometry across these cases would
show robustness to these choices, not establish statistical significance.
The [saved forecast comparison](esa-prediction-error-scale/README.md) checks
all available development forecasts against receiver-reported precision at
matching epochs. Later IMU-based prediction error is much larger, confirming
that receiver precision is only one part of the required forecast error model.
The [saved error-dependence check](esa-prediction-error-scale/CORRELATION.md)
measures the later combined forecast errors. Their strong time dependence is
not a measurement of receiver error alone and does not validate either
working covariance case above.
The [height-error transfer check](prediction-observed-development/ESA_HEIGHT_ERROR_TRANSFER_RESULT.md)
tested an earlier-only height correction at three cuts on the same flight.
It increased height RMS under both tested instrument error laws at all three
cuts. Keep the raw forecasts as the reference for adequacy checks.
The [GPS-only comparison](prediction-observed-development/ESA_ROLLING_GPS_CONTROL_RESULT.md)
shows why absolute error matters. After the 800-report cut, fixed GPS
velocity predicted the next 120 positions more closely in the horizontal
plane than either inertial error law. The other three cuts favored the
inertial forecast horizontally against both tested GPS rules.
The [raw twelve-window audit](prediction-observed-development/ESA_RAW_ACCURACY_RESULT.md)
found three horizontal failures under each law. The larger rolling miss
also exceeds the peak horizontal limit. The earlier GPS adjustment brings
one steady window inside the horizontal RMS limit. Every window meets both
height limits. The limits describe agreement with the receiver on the
development flight. Across-flight error coverage remains open.
The [training warning audit](prediction-observed-development/ESA_TRAINING_WARNING_RESULT.md)
shows that passing every limit during training still leaves later
forecast failures possible. Two of the three raw misses gave no warning
under either error law.
The [matched adjustment audit](prediction-observed-development/ESA_MATCHED_CONDITIONING_RESULT.md)
found that all available adjusted paths meet the descriptive limits on
the same 120 later positions per window. The point-law path is still
unavailable at the 800-report cut. Good point accuracy leaves the
longer-horizon height undercoverage and between-flight error law open.
The [matched uncertainty audit](prediction-observed-development/ESA_MATCHED_UNCERTAINTY_RESULT.md)
shows that height undercoverage at the 800-report cut also affects the
short horizon. There were 95 misses among the first 120 positions and
375 across the full 400. The earlier GPS adjustment alone leaves this
uncertainty unresolved.
The [height-role check](prediction-observed-development/ESA_HEIGHT_ROLE_RESULT.md)
uses the same stated band widths around both saved 800-cut paths. The
adjustment reduced height RMS and brought 25 positions into the bands,
while 95 remained outside. On the separate 400-cut comparison, scoring only
north and east preserved the original ranking in every complete setting.
This result leaves the physical height and independent coverage gates open.
The [GPS code reconstructions](prediction-observed-development/ESA_RINEX_CODE_COMPARISON_RESULT.md)
preserve the ranking against the same 120 later positions. They share
the aircraft antenna and GPS observations with the original export. A
[path sensitivity check](prediction-observed-development/ESA_SHARED_RECEIVER_ERROR_RESULT.md)
finds kilometre-scale margins for the fixed ranking and a metre-scale
margin for the position-accuracy screen. This leaves the airborne error
model unqualified.

The [satellite-product check](prediction-observed-development/ESA_PRECISE_GPS_SUPPORT_RESULT.md)
found final orbits for every GPS satellite used in the saved code solution.
Final clocks are missing for one of those satellites. An orbit-only
[replay kept the original set](prediction-observed-development/ESA_FINAL_ORBIT_REPLAY_RESULT.md).
The 120 later positions changed by 0.90 m RMS while the ranking and
preferred-model accuracy result held. This quantifies the effect of the
orbit substitution, with broadcast clock corrections and code unchanged.
The [matched clock replay](prediction-observed-development/ESA_RELATIVE_CLOCK_REPLAY_RESULT.md)
then changed only how the clock correction varied over time, using the
same reduced satellite set on both sides. It moved the later GPS positions
by 0.42 m RMS and preserved the ranking and preferred-fit accuracy
result. The imposed changes leave constant clock offsets unconstrained.
The [matched-field receiver replay](prediction-observed-development/ESA_SHAPE_RECEIVER_REPLAY_RESULT.md)
also preserves the non-smooth globe preference across eight receiver
paths. The globe residuals after smooth adjustment were 1.20 times the
working RMS scale for the export and 11–78 times that scale for the
seven code-based paths. The same working error model needs separate
qualification before it is used with different receiver products.
The [receiver-margin calculation](prediction-observed-development/ESA_SHAPE_RECEIVER_MARGIN_RESULT.md)
finds a score reversal with small changes timed to the shape signal.
For the original export, the worst-case threshold is 4.43 cm per
coordinate. A four-block acceleration correction reaches the tie with
a 27.20 m RMS position change in its constructed example. A receiver
qualification needs to constrain the time pattern as well as the size.
The [processed receiver check](prediction-observed-development/ESA_PPP_SHAPE_ERROR_RESULT.md)
moves that same score by at most 0.0301 units between exports on the
original comparison. The translated weights also give small relative
changes on 188 complete fast windows. The shared part of the receiver
error remains the qualification target.
The [carrier-phase replay](prediction-observed-development/ESA_CARRIER_PHASE_LATER_RESULT.md)
also agrees with the export within 12.3 cm RMS over the two-minute
window, with one earlier anchor. It moves the fixed shape score by
−0.208 units. This checks a distinct processing method with the same
GPS signals and leaves common satellite and atmospheric errors open.
The [continuous carrier path](prediction-observed-development/ESA_CARRIER_PHASE_CONTINUOUS_RESULT.md)
extends the test to all 520 reports. The earlier part contributes
less than 0.001 units to the score change after accounting for the
clock step. The one-flight result leaves the aircraft error law open.
The [GLONASS carrier replay](prediction-observed-development/ESA_GLONASS_PHASE_PATH_RESULT.md)
uses separate satellites and moves the original shape score by −0.067
units. Its later height differs from the GPS carrier path by 97.3 cm RMS,
which constrains claims about agreement across axes. Common errors and
independent flight coverage remain the calibration targets.

The [same-day balloon soundings](prediction-observed-development/ESA_SOUNDING_DELAY_RESULT.md)
change the standard model's overhead signal delay by 1.7–6.3 cm at the
reported flight heights during the two-minute forecast. The [replay](prediction-observed-development/ESA_SOUNDING_CARRIER_RESULT.md)
finds at most a 0.022-unit change in the fixed shape score and up to 15.5 cm
height RMS shift. These regional alternatives do not bound local weather
or justify changing the receiver covariance.

Two [GLONASS-only reconstructions](prediction-observed-development/ESA_GLONASS_COMPARISON_RESULT.md)
solved all 1,041 epochs with a separate set of satellites and the same
aircraft antenna. They preserved the forecast ranking. The two
GLONASS paths disagree with the receiver export by several metres.
These differences inform a processing sensitivity check while leaving
the absolute aircraft error unmeasured.

The [direct Doppler check](prediction-observed-development/ESA_DOPPLER_COMPARISON_RESULT.md)
recovered velocity separately from the GPS and GLONASS shifts. Anchored
at the last earlier receiver position, both integrated motions agree
with the original export within 0.30 m horizontal RMS and 0.27 m height
RMS on the same two-minute window. The signed velocity differences
are correlated across reports. This bounds the observed disagreement
between methods on this window. The aircraft antenna and anchoring
position are shared.

The [matched Doppler force check](prediction-observed-development/ESA_DOPPLER_FORCE_RESULT.md)
uses these velocities without the gyroscope. The force contrast
between the two shapes after an earlier offset is about 0.00005 m/s².
The velocity-source discrepancies exceed that scale, and the
accelerometer comparison leaves shape unresolved.

The [gyro direction comparison](prediction-observed-development/ESA_GYRO_FORCE_DIRECTION_RESULT.md)
adds the recorded angle increments to the same force supports.
The specified-field globe has much smaller angular errors under
the retained-field assumption. The check changes the observation
being compared and leaves absolute calibration and between-flight
coverage open.

The [matched-field profile](prediction-observed-development/ESA_MATCHED_GYRO_DIRECTION_RESULT.md)
preserves the shape preference over the full range of retained fractions
for this field. The narrowest gap corresponds to about 0.031° RMS of
tolerable change to the measured angles with fixed predictions. The
calibration task is to bound the effect of gyro gain and bias,
accelerometer direction and receiver errors against that scale.

The [endpoint replay](prediction-observed-development/ESA_GYRO_DIRECTION_CALIBRATION_RESULT.md)
finds one X-axis accelerometer correction that reverses the ranking
in all six settings. The allowance is a working bound. The actual
calibration and its compatibility with the earlier trajectory remain
open.

The [exact position replay](prediction-observed-development/ESA_X_BIAS_POSITION_REPLAY_RESULT.md)
checks six endpoint points against the earlier trajectory. All exceed
the original loss allowance. An affine lower bound quantifies the
nonlinear compensation that would be needed at this endpoint.

The [ground check](prediction-observed-development/ESA_GROUND_X_BIAS_RESULT.md)
finds that the endpoint also increases the spread in ground force.
Neither ground motion nor the force measurement error is calibrated
at the scale of this difference.

The [continuous X-bias profile](prediction-observed-development/ESA_X_BIAS_DIRECTION_PROFILE_RESULT.md)
puts the common safe edge at +0.0225 m/s² with other terms fixed.
The ground stops give almost the same force spread at that edge
as with X free. Earlier flight positions need to constrain the
remaining positive range before the direction check can be used
as a shape decision.

The [earlier affine position bounds](prediction-observed-development/ESA_X_BIAS_RANGE_POSITION_RESULT.md)
rule out that remaining range for the specified-field globe's saved
linear model. A corresponding bound on the nonlinear residual is
still needed. The other position fits have different X biases.

The [exact boundary search](prediction-observed-development/ESA_X_BIAS_NONLINEAR_RANGE_RESULT.md)
observed a 0.453 weighted nonlinear remainder at its best point.
The affine lower bound requires at least 1.047 to recover the
original loss anywhere in the remaining positive range. Extending
this point result to the entire range needs a separate bound.

The [earlier-only direction bias check](prediction-observed-development/ESA_DIRECTION_BIAS_TRAINING_RESULT.md)
tests the positive range using direction errors instead of earlier
position loss. Under the retained-field globe and fixed remaining
calibration, a direction-error bound around 0.013° could preserve the
earlier preference for smaller bias. Aircraft direction errors have no
verified bound at that scale. The other field settings estimate a
positive bias, so the result cannot be used as an instrument bound.

The [all-axis accelerometer check](prediction-observed-development/ESA_DIRECTION_ACCEL_CALIBRATION_RESULT.md)
uses an earlier direction fit and gives a smaller later direction error
for the globe in all 18 matched settings. It holds the gyro fixed. The
common gain direction is unobservable and most starts reach a working
bound. The fitted accelerometer values do not constrain real sensor error.

The [joint calibration replay](prediction-observed-development/ESA_DIRECTION_JOINT_CALIBRATION_RESULT.md)
adds gyro biases and gains. It retains a smaller direction error for the
globe in 17 settings and favors the disc in one retained-field sensitivity
setting. This makes a shared angular error allowance and a broader
calibration check necessary for any direction-based decision.
The [exact derivative audit](prediction-observed-development/ESA_DIRECTION_EXACT_GRADIENT_RESULT.md)
finds that none of the saved joint calibration points meets the stopping
limit on the exact earlier model. The later scores remain comparisons at
those points.
The [exact correction](prediction-observed-development/ESA_DIRECTION_EXACT_CORRECTION_RESULT.md)
then meets the local stopping limit for all 36 new fits and preserves
the 17-to-one ranking. This resolves the local stopping issue in that
direction experiment. It adds no independent angular accuracy bound.
The [velocity swap](prediction-observed-development/ESA_DIRECTION_VELOCITY_TRANSFER_RESULT.md)
changes the paired angular gap by at most 0.004° when only the scoring
source changes. Changing the training source moves it by up to 0.037°.
This demonstrates sensitivity to calibration and alignment through the
training velocity. It leaves common receiver and inertial errors open.
One [shared calibration across velocity products](prediction-observed-development/ESA_DIRECTION_POOLED_CALIBRATION_RESULT.md)
favors the globe under all tested pooled and two-source choices. The
smallest margin is 0.00125°, so the ranking remains sensitive to errors
whose scale has not been verified. The source products share an antenna.
Across [eight disjoint windows](prediction-observed-development/ESA_DIRECTION_WINDOW_TRANSFER_RESULT.md)
the ranking transfers at nominal and pooled calibration. Retained-field
globe errors grow by 2.3 to 10.1 times with the transferred calibration.
The error range needs to account for this within-flight variation.
The [angle-pair check](prediction-observed-development/ESA_DIRECTION_ANGLE_PAIRS_RESULT.md)
preserves the ranking without a fitted starting orientation. Its
smallest RMS margin is 0.0007°. Aircraft accuracy at that scale still
needs independent verification.
The [antenna offset replay](prediction-observed-development/ESA_DIRECTION_LEVER_ARM_RESULT.md)
raises the smallest margin to 0.0162° with the published offset. The
campaign's GIRAFE vertical force is a separate measurement that could
check one component. The campaign's fused roll and pitch use the same
iMAR and cannot independently check its attitude errors.
[Campaign data processing](https://essd.copernicus.org/articles/17/1667/2025/#section3)

On the exact two-minute score, the [fixed offset check](prediction-observed-development/ESA_CARRIER_LEVER_SENSITIVITY_RESULT.md)
puts a lower limit of 40.5 cm on an offset error that could close the gap
under the wider of the two tested gyro assumptions. The installation's
actual offset error and the antenna's phase response remain open.
The [measured-turn phase check](prediction-observed-development/ESA_GYRO_PHASE_TILT_RESULT.md)
sets bounds of roughly 11% to 23% of the score gap in an ideal antenna
model. At even the smallest starting tilt setting, more than half the
weight lacks a guarantee that every ray stays above the antenna plane.
The aircraft error budget needs evidence for the installed antenna.
An [elevation screen](prediction-observed-development/ESA_CARRIER_ELEVATION_SCREEN_RESULT.md)
keeps at least four satellites in every interval. Under the tested
weighting, it tightens the exact-anchor linear range error allowance by
a factor of about 7 to 13. This makes the screened range geometry a
tradeoff with the ideal phase model.
With the same satellite sets, the [range and motion weighting check](prediction-observed-development/ESA_CARRIER_WEIGHT_TRADEOFF_RESULT.md)
recovers much of the margin. The 1.35–1.71 mm screened range allowances
still assume exact anchors and the illustrative acceleration limit.
The [uncertain-anchor check](prediction-observed-development/ESA_CARRIER_REWEIGHTED_BUDGET_RESULT.md)
uses the original one-metre example per coordinate. All three screened
cases exhaust the margin before any ground-covered range error is added.
The screened method needs separately supported anchor and motion accuracy.
The [smooth-path search](prediction-observed-development/ESA_CARRIER_MOTION_WITNESS_RESULT.md)
found feasible errors that span 48% to 65% of the gap under its stated
limits. All solves reached the iteration cap. A full explanation
under those limits remains open.

A follow-up solver passed known-answer software checks. It returns a
feasible path and an independently checked upper bound on the possible
score change for the specified spline and error limits. The checks
cover coordinates with very different scales and an early optimizer
stop. The four recorded development searches still have their original
dispositions. This software check supplies no new aircraft measurements
or error limits.

The [continuous bound on flight 187](prediction-observed-development/ESA_CARRIER_CONTINUOUS_BOUND_RESULT.md)
places the maximum error contribution at 50.2% of the gap with the
full satellite set under the example limits. Each screened case still
straddles 100%. This focuses the confirmation requirement on the
actual accuracy of the full satellite set, including low-elevation
antenna effects and errors common to the aircraft receivers.

The [accuracy requirements replay](prediction-observed-development/ESA_CARRIER_ERROR_REQUIREMENTS_RESULT.md)
uses the saved bounds to quantify the remaining measurement task.
With the full satellite set and the other example caps fixed, the
ground-covered range error threshold is about 2.10 mm RMS. The
separate geometric terms also put the 0° screen just inside the
example limits at 99.25% of the gap. The installed aircraft response
and shared error caps still need independent evidence.

The [Nuuk apron comparison](prediction-observed-development/ESA_APRON_CARRIER_RESULT.md)
found roughly 7 mm RMS disagreement with a fixed parked position
after handling the recorded receiver clock. This measures the whole
residual on the ground. The moving-flight target concerns a specific
error direction. It still needs independent qualification in flight.
Matching the [parked aircraft to Nuuk Museum](prediction-observed-development/ESA_APRON_NKAR_RESULT.md)
shows little correlation on the 18 one-second steps. Subtracting the
station raised the RMS to about 9.5 mm on this excerpt. A nearby
receiver provides an external check and leaves local aircraft
effects and airborne transfer open.

The [two-minute follow-up](prediction-observed-development/ESA_APRON_IMU_OVERLAP_RESULT.md)
matched 1,440 satellite range changes during iMAR coverage. Removing
the museum residuals increased the aircraft RMS from 10.77 to 13.93 mm.
The simultaneous gyro rates varied considerably, so the GPS-selected
stop cannot be used as a control for zero angular motion. The limits on
airborne common errors still need evidence collected in flight.

The [GIRAFE inventory for the development flight](external-imu-data/ESA_GIRAFE_187.md)
identifies two acceleration files and two platform logs. The platform
measurements may constrain some motion errors once their axes, units,
time origin and movement relative to the aircraft are established.
The [matched force check](prediction-observed-development/ESA_GIRAFE_FORCE_OVERLAP_RESULT.md)
already shows that the two devices track changing force on all eight
windows. GIRAFE reads 26–29 mm/s² lower on average, and the median
centered disagreement is 1.8 mm/s². A useful error model must account
for the offset as well as the smaller changes around it.
The [force-only model check](prediction-observed-development/ESA_GIRAFE_FORCE_CONTRAST_RESULT.md)
uses offsets calculated on earlier supports. The later two-sensor
disagreement and shifts in predicted force between receiver products
both exceed the matched globe–disc contrast in every setting. These
check relative behavior within one flight. Absolute uncertainty still
requires independent aircraft data.
The [chronological transfer check](prediction-observed-development/ESA_GIRAFE_FORCE_ERROR_LAW_RESULT.md)
adds an observed test of the persistent component. A model that allows
an error shared across a window improves all eight later scores.
Its ranges cover seven later window means, versus two under the
independent-noise assumption. These are repeat scores on four windows
at two widths. They do not establish calibrated coverage.
The [airport reference check](prediction-observed-development/ESA_GIRAFE_GROUND_TIES_RESULT.md)
adds independently measured gravity at both stops. The instruments'
mean forces agree closely with the apron values. Their difference under
the airborne averaging measure is about 2 mm/s² on the ground and
26–29 mm/s² in flight. The ground offsets alone cannot explain
the airborne difference.
The [matched-averaging replay](prediction-observed-development/ESA_GIRAFE_FORCE_BANDWIDTH_RESULT.md)
explains about 98% of the median airborne gap by averaging the
fast iMAR vectors in GIRAFE's time cells before computing magnitudes.
Once both streams use matched time cells, the median gap is 0.47 mm/s².
The one window with variable atom interrogation retains a larger
difference. Any force-error estimate needs to specify the averaging
method and account for that operating condition.
The [matched error-law test](prediction-observed-development/ESA_GIRAFE_MATCHED_ERROR_LAW_RESULT.md)
uses the same chronological split as the raw comparison.
At a constant interrogation time, changing the covariance form has
little effect on the later log scores. The averaging method and the
recording condition matter more in this development test.
The [velocity uncertainty replay](prediction-observed-development/ESA_FORCE_VELOCITY_ERROR_RESULT.md)
shows why the receiver needs its own error model. Even with identical
reported velocity covariance at each epoch, changing its assumed
time dependence can substantially change the resulting uncertainty
in force. The paired model predictions also share a large error
component. Both effects matter to a force error model.
The [position derivative check](prediction-observed-development/ESA_FORCE_POSITION_DERIVATIVE_RESULT.md)
finds much closer agreement across receiver products and worse
agreement with the separate GIRAFE instrument. Cross-receiver agreement
leaves errors common to both products unmeasured.
The [direction replay](prediction-observed-development/ESA_DIRECTION_RECEIVER_DERIVATIVE_RESULT.md)
keeps the same globe–disc ranking across all receiver products and
both derivative methods. Position-derived predictions still miss the
measured angles by about a degree on the first straight window.
The [matched differentiation check](prediction-observed-development/ESA_MATCHED_RECEIVER_RESPONSE_RESULT.md)
reduces that error to 0.046° under the same retained-field, antenna-corrected
settings. An absolute accuracy rule needs a specified derivative method and
an independently justified error scale.
The [receiver-only selection](prediction-observed-development/ESA_DIRECTION_HOLDOUT_SELECTION_RESULT.md)
fixes eight new checks across both legs of recording 187. The
[sealed receiver forecasts](prediction-observed-development/ESA_DIRECTION_HOLDOUT_FORECAST_RESULT.md)
include an earlier error reference for each setting. The [new window scores](prediction-observed-development/ESA_DIRECTION_HOLDOUT_SCORE_RESULT.md)
find at least one shape within that range in 190 of 192 settings. On the
strongest turn, both zero-field derivatives favor disc, the retained-field
settings favor globe and the field-removal settings split by antenna
correction. Use motion and field dependence when developing an independent
accuracy rule. The observed range from this one installation gives no
between-flight coverage estimate.
The [field-range check](prediction-observed-development/ESA_DIRECTION_HOLDOUT_FIELD_RANGE_RESULT.md)
lets both shapes vary their gyro field retention over the full interval.
The smallest remaining shape gap is 0.0160° in the pair-angle RMS. The
search bounds quantify numerical uncertainty for these cases. Account for
sensor and receiver errors before applying this comparison to a new flight.
The [alternate receiver check](prediction-observed-development/ESA_DIRECTION_HOLDOUT_RECEIVER_RESULT.md)
finds up to 0.0090° RMS difference in the fixed angle predictions. The
shape preference holds on the four first-leg windows with matching times
in both alternate exports. The [whole-second selection](prediction-observed-development/ESA_DIRECTION_HOLDOUT_CLOCK_RESULT.md)
then gets complete coverage of the second-leg cells. The
[scores on the common clock](prediction-observed-development/ESA_DIRECTION_HOLDOUT_CLOCK_SCORE_RESULT.md)
keep the field-range ordering in all 96 settings across the three exports.
The turn's zero-field preference remains reversed. Shared receiver errors
and independent sensor accuracy still need separate evidence.

The [structured version](prediction-observed-development/ESA_STRUCTURED_AXIS_SCORE_RESULT.md)
reproduces all 80 scores with storage that grows linearly with path length.
The [full parallel-receiver check](prediction-observed-development/FULL_PARALLEL_GNSS_V2_RESULT.md)
finds centimetre-scale relative agreement in most of the opened flight but a
persistent decimetre-scale `mosaic03` divergence in its last fixed window.
A [speed-only split](prediction-observed-development/PARALLEL_GNSS_MOTION_PHASE_RESULT.md)
locates a smaller difference during fast flight and a larger one at low speed.
This challenges any claim that early receiver agreement guarantees the same
error behavior throughout a flight. It does not measure the common error of
receivers sharing an antenna or identify which stream is inaccurate. The two
policies above remain frozen; a time-varying alternative would require a new
version and independent prediction checks.
The [two-minute fast-flight audit](prediction-observed-development/PARALLEL_GNSS_120S_RESULT.md)
finds 95th-percentile end-to-start relative changes of about 1–2.5 cm per
axis across 195 windows. Persistent offsets between exports are larger.
This constrains *relative* receiver behavior over the forecast horizon, but
still does not identify their shared error or calibrate either policy.
The [reported-precision comparison](prediction-observed-development/PARALLEL_GNSS_REPORTED_PRECISION_RESULT.md)
finds that 5.9% of matched fast-flight `mosaic03` north positions differ
from `air1` by more than three times the scale from their summed reported
variances. Because the exports share an antenna, that ratio is diagnostic,
not a calibrated test or an absolute accuracy estimate.
The [fixed-window decomposition](prediction-observed-development/PARALLEL_GNSS_WINDOW_DECOMPOSITION_RESULT.md)
attributes 90–99% of fast-flight relative mean-square discrepancy to
window-level means. A new aircraft error law should test persistent
receiver discrepancy explicitly; this does not alter the frozen policies
above or establish a bound on error shared by the exports.

## From development comparisons to an independent flight test

1. The [repeat-turn study](prediction-observed-development/ESA_REPEAT_TURN_FORECAST_RESULT.md)
   compared four error allowances around the same predicted path. The
   turn allowance improved all four windows. Adding the steady allowance
   too gave the best score in three. The two IMU error descriptions agreed
   to the reported precision. In the best-scoring choices the mean squared
   standardized error ranged from 0.46 to 3.34. That spread shows why a
   better score alone does not establish that the error bars are reliable.
   In a [saved-score check](prediction-observed-development/esa-repeat-turn-scale-diagnostic.json),
   calibrating the combined allowance on three windows improved two of
   the four omitted-window scores and worsened two. The omitted-window
   mean squared standardized errors still ranged from 0.20 to 2.75.
   A single multiplier did not consistently account for the differences
   between these windows on the same flight.
   A [training-only scale check](prediction-observed-development/esa-repeat-turn-training-scale-diagnostic.json)
   used the archived fit for each window to estimate its own native
   variance. After allowing for the number of fitted parameters, these
   estimates were 11–22% of the fixed working variance. They worsened
   all eight later scores. The later mean squared standardized errors
   ranged from 3.8 to 103.3. Small training residuals alone did not
   predict later accuracy.
   The [covariance shape check](prediction-observed-development/esa-repeat-turn-covariance-shape-diagnostic.json)
   gave each error allowance its best possible overall scale on each
   scored window. The turn allowance still improved all four scores,
   and the combined allowance still led in three. The timing and
   direction of the added uncertainty therefore matter as well as its
   size. Those fitted scales describe the saved errors. A prediction
   still needs a scale chosen before its later positions are read.
   [Four steady-course controls](prediction-observed-development/ESA_STRAIGHT_CONTROL_PLAN.md)
   were selected from unused parts of the same recording. The comparison
   scores those forecasts using their own recorded motion and then using
   the [motion timing from the matched turns](prediction-observed-development/ESA_STRAIGHT_CONTROL_TIMING_CHECK.md).
   This second score checks whether the allowance would also help in
   steady flight if the analysis assigned it where little turning occurred.
   The [scored comparison](prediction-observed-development/ESA_STRAIGHT_CONTROL_RESULT.md)
   shows that reassigning a turn worsened all eight scores. The steady
   allowance improved every score, with mean squared standardized errors
   from 0.094 to 0.622. The timing result supports separate steady and
   turn terms. A [common-scale check](prediction-observed-development/ESA_COMMON_SCALE_CHECK.md)
   rules out a uniform covariance multiplier as an explanation of the
   observed error spread under the stated Gaussian reference. This holds
   even when steady flight and turns are checked separately. The
   [smooth-error check](prediction-observed-development/ESA_SCORED_PATH_SHAPE_RESULT.md)
   finds that smooth drift explains most of the largest steady-window
   error. The turning-window errors still vary widely after accounting
   for smooth drift.
   A [matched path check](prediction-observed-development/MATCHED_SHAPE_DRIFT_RESULT.md)
   shows that a free smooth correction could also absorb most of the
   difference between globe and disc forecasts at the same background field.
   Conditioning on earlier positions removes almost all of that smooth gap
   on the checked ESA pair, leaving about 0.76 m RMS outside smooth terms.
   The [boundary check](prediction-observed-development/SHAPE_FORECAST_BOUNDARY_RESULT.md)
   shows that the weighted difference persists after dropping the first
   20 later reports. A [local calibration bound](prediction-observed-development/CONDITIONED_SHAPE_CALIBRATION_RESULT.md)
   leaves at least 98.28% of that distance on the checked pair. Validate
   the nonlinear correction and the covariance at this smaller scale
   before scoring a new flight.
   The [remainder targets](prediction-observed-development/SHAPE_REMAINDER_HEADROOM_RESULT.md)
   make the two proof requirements explicit. The earlier residual
   bound controls which calibration points can enter the comparison.
   The later bound controls how far those points can close the gap.
   An [exact replay](prediction-observed-development/SHAPE_REMAINDER_WITNESS_RESULT.md)
   rejects a 0.1 earlier remainder bound over the full local box. The
   counterexample exceeds the original earlier fit-loss limit. A bound
   restricted to points that fit the earlier observations remains open.
   The [directional conversion](prediction-observed-development/SHAPE_REMAINDER_METRES_RESULT.md)
   gives a separate 4.03 cm coordinate target for the propagation error
   that can reach the later shape score under those assumptions.
   The shared-prefix predictor now uses the archived altitude correction.
   A [generated check](prediction-observed-development/SHAPE_GRAVITY_HISTORY_RESULT.md)
   reached 40 seconds with a sub-millimetre remainder. The error bound
   still needs to hold over the full flight at the recording's packet rate.
2. Before testing another flight, specify what would count as acceptable
   prediction in north, east and height. The criterion must account for
   training uncertainty, motion-dependent inertial measurement unit (IMU)
   error and GPS position errors, including those shared by receiver exports.
   The four turns and four steady windows on recording 187 can inform
   that criterion. They supply observations from one flight and leave
   between-flight variation open.
   The [separate quiet scale check](prediction-observed-development/ESA_AXIS_INNOVATION_SCALE_RESULT.md)
   improves the conditional covariance scores on all eight windows, with
   two inside the working error reference. Splitting the motion scale by
   slot worsens the hardest turn. The new rules remain development evidence.
   The [continuous range check](prediction-observed-development/ESA_AXIS_SCALE_COMPATIBILITY_RESULT.md)
   finds a retrospective scale setting for all four steady windows. It
   leaves compatibility on all eight windows unresolved and gives no new
   prediction coverage estimate.
   The [direct reference fit](prediction-observed-development/ESA_SCALE_REFERENCE_TRANSFER_RESULT.md)
   then puts all six donors inside the range for each fold. Only three of
   eight omitted windows meet it and the held-out log score worsens. Matching
   the donor reference cannot substitute for a separate prediction check.
   The [constant-shift check](prediction-observed-development/ESA_FORECAST_TIME_SHIFT_RESULT.md)
   leaves seven of eight windows outside the reference and slightly worsens
   the omitted score. A global shift of the saved path explains little of the
   remaining error under the working covariance.
   The [persistence check](prediction-observed-development/ESA_INNOVATION_PERSISTENCE_RESULT.md)
   improves the log score on every omitted window. It still leaves six of
   eight outside the reference. The motion term selects the longest memory
   tested, and the earlier variance scales stayed fixed.
   [Estimating memory and variance together](prediction-observed-development/ESA_JOINT_PERSISTENCE_RESULT.md)
   improves all eight omitted scores and puts six inside the reference.
   One steady window remains high and one turn is low. All numerical starts
   reach their cap, so the error policy stays in development.
   A [saved-point gradient check](prediction-observed-development/ESA_JOINT_PERSISTENCE_STOPPING_RESULT.md)
   found remaining descent in all eight donor fits. The [completed refits](prediction-observed-development/ESA_JOINT_PERSISTENCE_ANALYTIC_RESULT.md)
   leave the same two misses. The [sequential error audit](prediction-observed-development/ESA_PERSISTENCE_WINDOW_DIAGNOSTIC_RESULT.md)
   finds spread-out excess on the steady window and low scores during and
   after the turn, with other windows in both groups passing. The same
   motion label can appear with quite different errors.
   [Carrying earlier motion across the forecast cut](prediction-observed-development/ESA_PERSISTENCE_HISTORY_RESULT.md)
   leaves both misses unresolved under the fixed decay. The last active
   interval in the steady miss ended 79 seconds before the cut.
   A [whole-window scale mixture](prediction-observed-development/ESA_WINDOW_SCALE_MIXTURE_RESULT.md)
   improves the predictive score and places seven of eight windows inside
   its reference. With [two other GPS solutions](prediction-observed-development/ESA_FORECAST_RECEIVER_TRANSFER_RESULT.md)
   on the same times and unchanged forecast distributions, that count falls
   to three and two. Separate receiver-specific errors from common forecast
   errors before transferring the covariance.
   The [receiver-only covariance comparison](prediction-observed-development/ESA_RECEIVER_CONTRAST_COVARIANCE_RESULT.md)
   favors separate terms on summed omitted log score. The raw estimate
   violates positive semidefiniteness in the slowest band, so the model
   uses the planned clipping there. Keep that limitation and the shared
   error ambiguity when testing the term within the forecast covariance.
   The [compatibility test](prediction-observed-development/ESA_RECEIVER_COVARIANCE_COMPATIBILITY_RESULT.md)
   finds that only 18.7–25.8% of the estimated `air1` term can be removed
   before the remainder becomes invalid. A [refitted shared term plus
   the receiver terms](prediction-observed-development/ESA_ADDITIVE_RECEIVER_COVARIANCE_RESULT.md)
   improves the omitted marginal scores. The original receiver now
   falls below the error reference in six of eight windows. A better
   composite score alone cannot qualify coverage.
   A [raw carrier comparison](prediction-observed-development/ESA_RAW_PHASE_PPP_CLOSURE_RESULT.md)
   on a separate interval shows that the three position solutions
   capture only part of the one-second differences in the raw carrier
   measurements. The [fixed longer blocks](prediction-observed-development/ESA_RAW_PHASE_PPP_TIMESCALE_RESULT.md)
   give no consistent improvement. The [chronological transfer result](prediction-observed-development/ESA_PPP_COVARIANCE_CHRONOLOGY_RESULT.md)
   finds that faster variations carry over from the first 97 windows to
   the last 98. The final batch's window-wide offsets exceed the trained
   uncertainty scale by a factor of 71 in squared units. Those offsets
   need a changing error term with an independent forecast check. A
   [conditional offset forecast](prediction-observed-development/ESA_PPP_OFFSET_FORECAST_RESULT.md)
   cuts the short-lead RMS but still gives a standardized squared error
   near 29 at two minutes. The fitted transition covariance cannot be
   used as the aircraft forecast uncertainty.
   A [nearby fixed receiver](prediction-observed-development/ESA_FIXED_REFERENCE_CLOCK_RESULT.md)
   supplies a separate check during the Reykjavík ground stop. The two
   position paths differ by 0.85 m vertically RMS after replaying the
   receiver clock correction. The [integrated Doppler path](prediction-observed-development/ESA_FIXED_REFERENCE_DOPPLER_RESULT.md)
   drifts by more than 20 m vertically and cannot resolve their difference.
   These observations concern a ground stop. The in-flight common position
   error and full forecast uncertainty still need an independent bound.
   A [longer forecast on the same flight](mixed-tangent-hybrid/ESA_DISPATCH_ACCURACY_RESULT.md)
   met the full-horizon descriptive limits with the persistent receiver error
   policy and the specified-field globe. The short-correlation policy missed
   the horizontal RMS limit. Both policies remain development settings.
3. Freeze the error law, the training and prediction split, the matched
   model comparisons and the rule for recording failures and abstentions
   before opening any reserved flight. Report how many flight groups pass
   the fixed test, including groups with missing forecasts. The
   [flight-group count](PREDICTION_GROUP_COUNT.md) explains the limit of
   what seven groups can establish about prediction coverage.

## Frames and data boundaries

- Retain the receiver's full north/east/up covariance. The three cross terms
  are north–east, north–height and east–height; height is upward.
- Reject nonfinite or nonpositive-definite reported covariance. Do not repair
  it by adding the floor or clipping eigenvalues.
- Use the same receiver-coordinate weight for every physical candidate. The
  conversion to latitude, longitude and ellipsoidal height uses the receiver's
  declared WGS84 chart. It is an observation convention, not new curvature evidence.
- Use actual, strictly increasing timestamps within one GPS week. Do not
  interpolate measurements or fill gaps. Interval selection handles gaps separately.
- Construct training weights from training rows only. Gyro values, fitted
  residuals, later positions and preferred-model labels are not policy inputs.

## Implementation and verification

The shared `lll.airquantumgrav_error_policy` adapter uses the existing
`lll.ilvis0_error_model` and `lll.ilvis0_structured_covariance` components.
Policy identifiers and numerical values are versioned. Receiver measurements
are preserved, with a hash of the fields used by the policy.

The passing software tests check full cross-axis handling, height sign, time ordering,
invalid covariance rejection before floors, unchanged input rows and independence
from model/outcome metadata. They compare small dense covariance matrices against
the structured operator for residuals and all 27 derivative columns. A dense
request specifies an epoch cap, at most 2,048, and fails before allocation
when exceeded. Long records use the structured operator.

The [76 software checks](esa-error-policy-checks/README.md) have saved source,
environment and test-report bindings. The policies are now used in the
[completed first pilot](esa-development-pilot/README.md) and the
[completed gravity revision](esa-observed-height-pilot/README.md). The
[wider-precision revision](esa-observed-wide-pilot/INTERPRETATION.md) completes
three adequate matched comparisons under the same policies. Their use does
not establish that either covariance describes the true receiver error or
the complete uncertainty of an inertial prediction.
No protected confirmation data is released by these software checks or pilots.

The [completed known-noise test](esa-noisy-prediction/INTERPRETATION.md) retains
these weights while adding generated receiver and IMU errors. All 24 fits
converge, but none passes the physical accuracy screen. Receiver-only weights
are not a qualified complete prediction-error model under those stress settings.
The weights and failed outcomes remain unchanged; full sensor-error propagation
and fitted-calibration uncertainty are the next gates.

[Software verification](esa-error-policy-checks/README.md).

[Receiver assessment](esa-position-assessment/INTERPRETATION.md) ·
[Training-only controls](esa-training-forecast-controls/README.md) ·
[Roadmap](ANALYSIS_ROADMAP.md).
