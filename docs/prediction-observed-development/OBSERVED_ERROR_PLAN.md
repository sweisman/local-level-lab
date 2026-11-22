# Qualifying prediction error without assuming its cause

The generated controls show that synthetic forecasts can drift, but do not
yet isolate every cause. They do not measure the error law of the recorded ESA
instrument. The ESA development
IMU was moving with an aircraft, so short changes in its angular rates can be
real motion, vibration, sensor error, or a mixture. The existing
[rate comparison](GENERATED_RATE_COMPARISON.md) and
[training residual check](TRAINING_INNOVATION_RESULT.md) already show that the
two working noise laws are inadequate as a complete explanation. A smaller
fitted training cost is not a reason to choose one of them.
The [saved generated fitted-error audit](../prediction-simultaneous-law-family-v3/FITTED_INNOVATIONS_RESULT.md)
provides a useful software reference: 190 passing fits show much weaker
height-error persistence than the ESA development fit. It does not calibrate
an observed-aircraft error-law test because the generated training histories
and error processes differ. A matched [complete-fit generated pilot](FULL_FIT_INNOVATION_NULL_RESULT.md)
has now finished: both numerical fits converged, but neither passed the
predeclared physical trajectory screen. A qualifying full-trajectory error
model and further independent generated controls are still required.
The generated complete-fit code uses a 0.1 m horizontal RMS physical screen;
some earlier reports described it as 10 m. See the
[accuracy-rule correction](GENERATED_ACCURACY_RULE_ERRATUM.md). The earlier
large path misses fail either value.
The [saved path-error audit](GENERATED_PATH_ERROR_AUDIT_RESULT.md) locates the
pilot's large miss in its fitted trajectory: generated training receiver
errors are under 0.4 m horizontal RMS, but fitted paths are 33–55 m from
known truth. Error-law development must cover this path uncertainty.
The [bound-aware generated technical pilot](BOUND_AWARE_GENERATED_PILOT_V2_RESULT.md)
then retained all calibration directions and covered both fresh generated
truths with affine intervals. Its point paths still missed the physical
screen, and two cases cannot establish nonlinear or aircraft coverage.
The [saved whole-forecast audit](GENERATED_SIMULTANEOUS_BOUND_RESULT.md)
expands those marginal ranges to nominal simultaneous coverage over all 900
later coordinates under the same generated Gaussian assumptions. Both truths
remain inside, but neither point path passes physical accuracy. This does not
qualify coverage for the observed aircraft.
The [saved calibration-direction audit](GENERATED_WEAK_DIRECTION_RESULT.md)
finds the same weak combination of gyro gain, gravity adjustment and vertical
accelerometer bias in both generated fits. It suggests a focused nonlinear
calibration stress test; it does not assign the large path errors to one cause.
That [finite native stress test](GENERATED_WEAK_DIRECTION_NONLINEAR_RESULT.md)
has now closed. Moving 0.20 normalized units along the shared weak direction
changes the later path by less than 0.7 m in either generated case, against
original misses above 90 m. The local tangent is accurate over this tested
range. Other calibration directions, fit basins and error-law assumptions
remain open.
The [saved interval-width audit](GENERATED_BOUND_COMPONENTS_RESULT.md) shows
that calibration uncertainty supplies about 71–81% of the median marginal
range half-width under the assumed generated law. This explains much of the
range's size within that calculation; it does not measure aircraft error or
repair either inaccurate point path.
The [known-calibration audit](GENERATED_CALIBRATION_RECOVERY_RESULT.md)
compares the two fitted sensor settings with the values used to generate
their records. Their normalized RMS differences are 0.47 and 0.35 of the
declared parameter half-ranges; three fitted parameters reach limits despite
interior generating values. This demonstrates calibration recovery trouble in
the two cases, without identifying the cause of the later path misses.
The [fixed-parameter substitution](GENERATED_CALIBRATION_SUBSTITUTION_RESULT.md)
replays those cases using their known sensor settings while leaving other
fitted parameters untouched. Both paths get much worse. This exposes strong
coupling among fitted corrections, not a usable aircraft calibration rule.
The [eight-case generated cohort](GENERATED_BOUNDED_COHORT_RESULT.md) then
repeats the full 600/300-report calculation with fresh noise seeds on the
same route. All eight fits converge, none passes physical path accuracy and
all eight known futures fall within broad assumed intervals. The observed
aircraft error law remains unqualified.
The [saved noise-floor audit](GENERATED_NOISE_FLOOR_AUDIT_RESULT.md) shows
why the inherited 0.1 m screen cannot by itself qualify these noisy paths:
their own assumed fixed-calibration conditional error scale is 17.39 m.
That scale does not account for fitted-calibration uncertainty or establish
aircraft coverage. A newly frozen noisy-path criterion is needed; the eight
original failure labels remain unchanged.
The [next qualification plan](NOISE_AWARE_ADEQUACY_PLAN.md) separates
point error, uncertainty coverage and interval usefulness, and requires
fresh generated confirmation after the metric is checked in software.
Its [first software check](FORECAST_ENVELOPE_CONTROL.md) passes six
deterministic cases. The [dual-target generated pilot](DUAL_TARGET_GENERATED_RESULT.md)
then closes two full fitted cases with both forecast targets saved before
later data. Its ranges are broad; independent generated coverage, nonlinear
calibration checks and aircraft error-law qualification remain open.
The [local tangent control](LOCAL_PROJECTION_NULL_RESULT.md) projects 2,048
white histories per law through the saved 26-direction ESA fit. None reaches
the observed height correlation at one or twenty reports apart. This rules
out fitting projection alone under the declared fixed covariance, while
leaving nonlinear refitting and physical error sources open.
The [saved error-pattern audit](INNOVATION_MORPHOLOGY_RESULT.md) finds that
height errors have substantial low-frequency power. A short positive
exponential matches the first twenty lags approximately but fails farther
out; it is a stress target for generated controls, not an adopted error law.
The [matched long error-scale check](ORACLE_MATCHED_SCALE_REPORT.md) gives
nearly the same 350.7 m horizontal RMS scale under both synthetic laws, but
the two saved outcomes are 59.7 m and 637.1 m. Two draws do not establish
coverage, and neither law is thereby qualified for the recorded flight.
The [saved generated horizon table](ORACLE_HORIZON_REPORT.md) shows why the
forecast question matters: with 600 earlier receiver updates, the synthetic
horizontal RMS scale is 0.89 m over 60 withheld seconds, 2.70 m over 120,
and 17.59 m over 300. Without those updates it is 350.70 m over 300.
A separate sealed generated study with 800 earlier updates gives 2.71 m
over the next 120 seconds under its increment-error law. This agreement
checks the calculation across two generated paths; it does not establish
observed-flight coverage.
The [retrospective ESA development table](RECORDED_HORIZON_DIAGNOSTIC.md)
scores the already sealed forecast over shorter prefixes: 0.28 m horizontal
RMS over 120 reports, 1.94 m over 200, and 14.25 m over 400. This cannot
retroactively validate a shorter window. A new receiver-selected development
window and short-block rule must be frozen before looking at its errors.
The [new short-block selection](../esa-short-block-development/README.md)
does that for all three additional windows already chosen from receiver
metadata. It fixes 800 training and 120 future reports per window, but does
not authorize preparation or fitting while the error law remains unqualified.
Its [chronology note](../esa-short-block-development/INTERPRETATION.md)
states that the 120-report duration was chosen with the first window's
outcomes already known. It is development, not independent validation.
An earlier-origin [400/120 check](ROLLING_ORIGIN_400_CONDITIONAL_RESULT.md)
on the already opened first window sealed both fits and both early-only
conditioning tasks before scoring later positions. Conditioned horizontal
and height RMS are 0.56 m and 0.17 m. Both candidate IMU error laws give
nearly identical forecasts, and nominal 95% ranges cover all 120 reports,
which remain strongly time-correlated. This favorable short window does not
identify the error law or validate coverage over a new flight or a longer
horizon. It does not lift the gate on the three other development windows.
The supplied law's marginal one-standard-deviation ranges span about
0.06–3.23 m north, 0.06–3.17 m east and 0.15–0.52 m up over those 120 reports.
All-report nominal coverage is therefore also a statement about those fairly
broad assumed ranges; their width has not been calibrated from independent
aircraft flights.
Two [unchanged receiver-only rules](ROLLING_ORIGIN_400_RECEIVER_CONTROL.md)
were also scored on that same window. Their 417–424 m horizontal RMS misses
are much larger than the conditioned IMU forecast's 0.56 m. The control
compares fixed forecast rules; it cannot assign the improvement to the gyro
alone or calibrate uncertainty.
A [later-designed control](ROLLING_ORIGIN_400_VELOCITY_CONTROL.md) starts from
the receiver's reported GNSS velocity and misses by 418 m horizontally on
the same window. All three receiver-only controls hold course fixed. Their
failure does not rule out a more adaptive receiver-only predictor or prove
which IMU channel supplies the improvement.
A [constant-turn follow-up](ROLLING_ORIGIN_400_TURN_CONTROL.md) estimates one
course rate from the last 60 earlier GNSS velocity reports. It misses the
later window by 448 m horizontally. This later-designed rule still cannot
exclude other GPS-only predictors or isolate the gyro contribution.
The [saved six-channel check](RECORDED_CHANNEL_DEPENDENCE.md) also finds a
gyro/accelerometer correlation of −0.628 at the shortest tested span. This
shows shared short-timescale variation, while leaving aircraft motion,
vibration, processing and sensor coupling unresolved.
The [200/120 earlier-origin result](ROLLING_ORIGIN_200_INTERPRETATION.md)
shows that a fit made earlier in the same opened flight predicts a different
120-second block with 0.467 m conditioned horizontal RMS. Both fits and both
conditioning tasks pass. The result supports temporal transfer within this
flight, while the strongly correlated errors and unverified law leave
independent-flight coverage open. Further overlapping starts are low value.
An [analytic sampled-data control](ERROR_ATTRIBUTION_CONTROL.md) constructs
real vibration and correlated sensor-error explanations with identical IMU
and one-second receiver reports. It establishes why these channels alone
cannot assign the short-time variation to one cause.
A [withheld-forecast control](FORECAST_AMBIGUITY_CONTROL.md) then gives
identical recorded IMU and earlier receiver data to two hypothetical paths
that finish 2.79 m apart after 120 seconds. Its error onset is adversarial,
not measured from either aircraft instrument. Shorter prediction therefore
still requires a justified range for changing error and aircraft motion.
The [full receiver-only audit](FULL_RECEIVER_CONSISTENCY_RESULT.md) and
[ground interval control](GROUND_RECEIVER_CONTROL_RESULT.md) show centimetre-scale
relative PPP stability on the opened recording, without establishing airborne
or absolute accuracy. The [overlapping raw iMAR check](GROUND_IMU_RATE_RESULT.md)
records a 16.37°/h unadjusted mean-rate magnitude, but its minute means and
brief large yaw event show that low ground speed does not make angular motion
known. These controls constrain the observable scales; they do not identify
sensor error separately from platform motion.

## Next finite qualification

1. Use only recording 187 and its already selected training interval. Keep
   the later receiver reports and seven reserved ESA flight groups closed
   during law fitting. Preserve every original rate sample and timestamp.
2. Build generated aircraft controls with known white sensor error, changing
   bias, receiver error, correlated vibration and independently generated
   small course changes. The
   motion used to test the diagnostic must not be produced by the same code
   that estimates it.
   The [analytic known-motion control](MOTION_ERROR_CONTROL.md) now supplies
   these separate components and passes three deterministic checks. A fitted
   error-law method has not yet been tested against it.
3. Compare three-point rate contrasts, their cross-axis dependence and the
   fitted receiver innovations at several time scales. Estimate a component
   only where **additional independent constraints** break the ambiguity
   demonstrated by the analytic control. Otherwise return an interval or
   **unidentified**.
   The [matched generated comparison](MOTION_ERROR_CONTROL.md) shows that
   both physical vibration and correlated sensor error can dominate these
   contrasts at different spans. It does not estimate either component from
   the combined observations.
4. Freeze candidate laws, parameter bounds, earlier-only fitting, absolute
   residual checks and a finite work allowance before applying the method to
   recording 187. Treat the second selected run as development data from the
   same flight, never as independent confirmation.
5. Before predicting later receiver positions, require the chosen law to
   pass held-out generated controls that include motion mismatches and a
   changing-bias adversary. Choose a withheld duration using generated
   uncertainty and receiver-only geometry, never the saved development
   errors. Save the prediction and its uncertainty range before reading
   later receiver reports.

Intrinsic gyro noise need not be identified separately if an **effective
prediction-error envelope** can be qualified for the full motion, IMU and
receiver process. If the controls cannot justify such an envelope, report
the recorded components as unidentified and leave the prediction gate open.
The [conditional error-bound calculation](PREDICTION_ERROR_ENVELOPE.md) now
passes six generated checks, including independent integration of a moving
aircraft. It propagates supplied limits without silently dropping changing
gyro error, force error or receiver error. Its generated check supplies the
realized error maxima, so it does **not** establish those limits prospectively
for the ESA recording or open the reserved-flight gate.
Applying a valid samplewise Gaussian maximum to the declared synthetic IMU
settings yields a 3.16 km bound over 120 seconds even before receiver or
motion-model error is added. That route is too loose for the intended
prediction test. The next candidate must keep time correlation and forecast
growth explicit. The [flight-group count check](../PREDICTION_GROUP_COUNT.md)
also shows that seven reserved groups cannot alone provide a distribution-free
95%-coverage claim with 95% confidence.
The [structured changing-drift candidate](INTEGRATED_DRIFT_LAW_PLAN.md)
passes independent covariance and earlier-only conditioning checks, and a
separate generated-IMU propagation control passes. Its
[frozen eight-case pilot](integrated-drift-pilot/RESULT.md) completed all tasks
but kept every withheld coordinate within nominal marginal ranges in only
3/8 generated histories. A conservative simultaneous bound retained 6/8.
This candidate does not qualify an aircraft
prediction range. A separate revised law was therefore tested on new
generated seeds; the seven reserved ESA groups remain closed.
The [revised law](INTEGRATED_DRIFT_V2_PLAN.md) includes changing gyro bias
through an integrated snap-error approximation. Its
[fresh-seed pilot](integrated-drift-v2-pilot/RESULT.md) passed 16/16 technical
tasks and kept 16/16 histories inside the predeclared simultaneous range.
Sixteen cases are too few to establish a 95% failure bound. A larger
independent generated cohort must pass before any observed-aircraft range
is considered.
That [256-case generated check](integrated-drift-v2-validation/RESULT.md)
completed but failed its predeclared gate: 0/128 no-vibration histories and
4/128 vibration histories exceeded the simultaneous range; the limit was
one each. Its range half-width at the last withheld second was 25.59 m per
coordinate. Preserve the failure and diagnose the saved residuals before
testing another law. No ESA reserved group may be opened on this basis.
The [saved failure diagnosis](integrated-drift-v2-validation/VIBRATION_DIAGNOSTIC.md)
finds three exceedances at the first withheld second and one at second 69.
The [clean 100 Hz control](integrated-drift-v2-validation/CLEAN_PROPAGATION.md)
has less than 0.0004 m of integration error in either motion mode, far below
the missed errors. First-second standardized RMS is near one on every axis
in both strata; no broad early variance deficit is apparent. The frozen
gate failed to certify a rate below 5%, which does not establish that the
true generated failure rate exceeds 5%. Paired fresh-seed controls can test
the vibration association. The 25.59 m final half-width also needs a
separate usefulness check before any Earth-model interpretation.
The [fresh 16-pair matched-noise control](paired-vibration-control/RESULT.md)
had no range failures in either setting and a maximum paired change of
0.000224 in standardized score. The generator's 10 Hz vibration repeats at
integer-second receiver reports, where its position change is a constant
0.2 mm north offset. This makes the current vibration label a weak stress
of receiver-level prediction. The four-versus-zero outcome in the separate
256-case cohort remains unexplained and its failed gate is unchanged.
Develop a motion perturbation visible at the receiver times before using
new generated cases to judge coverage.
The next [receiver-visible motion pilot](nonaliased-motion-control/PILOT_RESULT.md)
adds a 0.37 Hz trajectory change of 0.2 m peak-to-peak at receiver times.
All 16 matched-noise pairs passed technically, with no range misses and a
maximum paired standardized-score change of 0.0016. This checks a small
generated motion difference; it cannot certify the law's tail coverage.
Before another large generated campaign, assess whether the law's width
preserves the intended model contrasts. The [endpoint overlap benchmark](INTERVAL_USEFULNESS.md)
is only a first check, not a full trajectory decision rule.
The [saved ESA model forecasts](INTERVAL_USEFULNESS.md) show kilometre-scale
center separation in one complete development setting. A separate fresh
[256-history generated check](threshold-42-validation/RESULT.md) passed its
predeclared gate after raising the simultaneous threshold to 4.2. The
previous 3.635-threshold gate remains failed. The new range still needs a
justified real-aircraft error and calibration model, plus matched full
trajectory contrasts, before any reserved flight can be used for a decision.
The GNSS-only PPP export includes reported north/east/up velocity and six
velocity covariance fields. The decoder now retains those fields. Before
using them as added motion constraints, check their timing, units,
correlation with positions, and empirical consistency on training data.
Their presence alone does not make them independent evidence.
An [earlier-only consistency check](GNSS_VELOCITY_CONSISTENCY.md) now finds
0.016/0.007/0.036 m/s north/east/up RMS differences from centered WGS84
position derivatives on 398 training epochs. This supports the timing and
field interpretation; cross-time/cross-field dependence and covariance
calibration remain open.
A [separate 5 Hz course-rate comparison](GNSS_5HZ_MOTION_RESULT.md) now
uses the earlier-only window from the same opened flight. GNSS course change
tracks much of the logged body-down gyro variation over two- and ten-second
spans, but the changing differences remain 378 and 223°/hour RMS. Crab,
attitude coupling, timing and sensor effects are still mixed. The result is
motion context, not an identified IMU-noise law or qualified forecast range.
On the separately generated, known-motion aircraft control, the same
comparison leaves less than 0.001°/hour RMS changing difference with exact
IMU readings and 1.50/1.30°/hour after its declared synthetic sensor errors
are added. Five focused software checks pass. This confirms the comparison's
sign and timing on an idealized path; the generated aircraft has no crab or
roll, so its small residual cannot serve as a bound for the recorded flight.
A separate [sampled-data control](../../analysis/lll/esa_gnss_alias_control.py)
shows a remaining limit of the 5 Hz receiver stream. It constructs two
physical histories with exactly the same 300 Hz IMU readings and 5 Hz receiver
positions **and velocities**. One has real 10 Hz pitch/forward motion; the
other has correlated IMU error and a fixed 0.2 mm receiver-position offset.
The control is hypothetical, not an estimate of aircraft vibration or ESA
sensor error. It proves that higher receiver sampling alone cannot uniquely
assign all short-time IMU variation to motion or instrument error. Its
[deterministic test](../../analysis/tests/test_esa_gnss_alias_control.py)
passes without opening an aircraft recording.
A [matched training-only covariance audit](GNSS_COVARIANCE_AUDIT.md)
finds no negative eigenvalues in 400 printed position and velocity matrices.
Its lagged position-velocity contrasts still do not calibrate accuracy:
the two fields share one PPP solution, and their joint cross-time covariance
is absent from the export.
A [matched parallel-receiver check](PARALLEL_GNSS_RESULT.md) finds two more
PPP exports at all 400 earlier times, with centimetre position differences.
These receivers share an antenna, and their PPP errors may be correlated;
agreement does not establish absolute position accuracy or an IMU error law.
A [common-time follow-up](PARALLEL_GNSS_TIME_RESULT.md) accounts for the
small timestamp offsets with reported velocities. It reduces east-axis
differences but leaves common receiver and processing errors unidentified.
A [saved-fit cross-check](PARALLEL_GNSS_FIT_RESULT.md) finds about 0.8 m north
and 1.0 m east RMS raw training error against each of the three receivers.
Their centimetre-scale disagreement cannot explain that raw discrepancy,
while shared PPP error, aircraft motion and the observation model remain
possible contributors. This does not score the conditioned later forecast.
A [separate sealed-forecast check](PARALLEL_GNSS_FORECAST_RESULT.md) now does:
the unchanged early-only conditional forecast has 0.554–0.563 m horizontal
and 0.169–0.197 m height RMS against all three receiver streams on the same
120 later times. The comparison was designed after the `air1` outcome and
does not establish calibrated prediction coverage or an independent flight.
No numerical preference from the 53-stretch study or the seven reserved ESA
groups is revised by this development work.

The later [matched 400/120 three-model comparison](ESA_400_120_MODEL_MATRIX_RESULT.md)
used that same opened development flight. All 24 frozen fits closed: 20
passed numerical checks, and four zero-removal flat-disc fits did not
converge. Both complete profiled-removal settings favor globe on later
receiver positions and pass the preferred-fit physical screen. The two
zero-removal settings abstain. The [sealed runtime](ESA_400_120_MODEL_MATRIX_RUNTIME.md)
and portable evidence preserve every outcome. The horizon was chosen after
earlier results on this flight, and the real-aircraft error range remains
unqualified. The seven reserved groups remain closed.
