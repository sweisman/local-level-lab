# Methodology: decisions and how to check them

This page is for anyone who wants to validate the method rather than take it on trust. Each section states a decision, why it was made, what was rejected, the simulation evidence, and the automated test that guards it.

- [MATH.md](MATH.md) has the equations.
- [EVIDENCE.md](EVIDENCE.md) has every number quoted here. Regenerate it with `python analysis/tests/evidence.py`.
- Run the tests with `pytest analysis/tests server/tests`.

**Scope.** This is an experiment for a small number of careful operators first: the protocol (calibrations, a rigid mount, turning the IMU in flight, a serial or BLE link held for hours) asks a lot. Crowdsourcing can follow once the instrument is characterized. No flight result should be read before the bench validation in [BENCH.md](BENCH.md).

Criticism is welcome. The most useful kind is a synthetic session (`lll synth …`) that the pipeline gets confidently wrong.

## What is being tested, and what isn't

The question is: **given an aircraft trajectory in latitude/longitude coordinates, does an independent inertial sensor measure the rotation that a rotating globe, a still globe, or a still flat disc predicts?**

- **GNSS supplies only the coordinates and velocities.** Someone who rejects the globe can still use latitude and longitude as an addressing system. Each model then makes its own prediction from the same trajectory. The gyro doesn't know which model the coordinates were "built on". It measures rotation relative to inertial space.
- **The predictions never use the gyro.** The orientation of the IMU uses the gyro only for fast, large rotations (banked turns at °/s, the participant turning the IMU at tens of °/s), never the slow °/h signal. See MATH.md, "The IMU's orientation".
- **Four models defined, three tested.** The models are a rotating globe, a still globe, a still disc and a spinning disc. The two disc models differ only by a constant rotation about the vertical, which this protocol can't separate from gyro bias and g-sensitivity along gravity (section 6). They make the same testable predictions, so the still disc is tested and stands for both. Whether a disc spins is therefore not tested.

## 1. One standardized external IMU instead of phones

**Decision.** Record with a WitMotion WT901 (two variants) over Bluetooth. The phone only supplies GNSS and runs the app.

**Why.**
- Phone gyros differ by more than 10× in bias stability between models (published Allan-variance studies range from about 2 °/h to 28 °/h), and their processing is opaque.
- One device model makes units comparable and lets each unit be characterized.

**Rejected.**
- Phones, for the reasons above.
- Industrial IMUs such as a Murata SCH16T or an ADIS16465, which are better but cost more and need custom logging hardware. They remain an option for a reference unit.

**Caveats.**
- WitMotion firmware applies factory calibration, filtering and possibly automatic gyro zeroing. The app turns zeroing off, reads every setting back at each connection, and logs it.
- At ±2000 °/s, one 16-bit count is 220 °/h (see section 12).
- The bench test planned for when the devices arrive will measure the real units' noise, bias stability and quantization.

## 2. Store bytes, decode in the open

**Decision.** The phone stores every Bluetooth read verbatim with its arrival time. All decoding happens in `analysis/lll/witmotion.py`.

**Why.** Nothing is lost or altered on the device, and anyone can rerun or replace the decoder. The Kotlin parser is for the live display only. Both are tested on the same hand-built packets.

**Clock.** Bluetooth only adds delay, so sample times come from a straight-line map of device time onto phone time, fitted to the earliest arrivals. Two failure modes are handled explicitly:
- **BLE samples are timed by counting packets,** so each lost notification would make every later sample early by one period. Steps in the earliest-arrival envelope reveal how many were lost and where, and the sample index is restored. Losses are also reported.
- **A serial IMU might send its clock packet less often than its gyro packets.** Each gyro sample is then dated from the nearest preceding clock packet plus whole sample periods, never interpolated across a gap.

**Evidence.**
- Within 5 ms over an hour, under random batching, stalls and a ±120 ppm crystal (`test_clock_map_recovers_sample_times`).
- BLE losses of 0.1 % and 1 % are recovered almost exactly, with 95th-percentile timing errors of 0 and 12 ms (EVIDENCE §12; `test_ble_lost_samples_are_recovered`).
- Clock packets every fifth sample time as well as every sample (`test_sparse_spp_clock_packets_time_correctly`).

## 3. The disc's own transport term

**Decision.** The flat model includes `ω_disc = (0, 0, −dλ/dt)`. On a pole-centred disc, a constant-bearing eastward track circles the centre; westward, it turns the other way.

**Why.** The independent geometric check found the term missing from v0.1, which predicted zero for the disc. At 40°N and 230 m/s eastbound it is 9.7 °/h. Leaving it out made the disc artificially easy to reject.

**Why dλ/dt is taken straight from the GNSS longitudes.** The analysis differentiates the logged longitude coordinates (30-s smoothing). The disc's prediction then depends only on successive coordinates and time: no velocity, no Earth radius and no disc scale.

An earlier version recovered dλ/dt from the east velocity by undoing the receiver's WGS-84 conversion. That would smuggle in a globe radius if a receiver derives its velocity from Doppler rather than from coordinates.

**Evidence.**
- All three tested models agree with geometry to 9 × 10⁻¹² rad/s (EVIDENCE §1; `test_flat_models_match_geometry`, `test_sphere_models_match_geometry`).
- With deliberately absurd velocities passed in, the disc prediction from the longitude rate still matches (`test_disc_from_longitude_rate_needs_no_velocity`).

## 4. Synthetic truth from geometry, not from the model code

**Decision.** Test data takes its true rotation from `analysis/tests/truthgen.py`, which never imports `lll.models`.

**Why.** If the generator used the same formulas as the analysis, a sign or frame error in them would be invisible. The geometry generator builds the NED axes in an inertial frame and differentiates them numerically, with no rate formula anywhere.

## 5. Ground calibration as a palindrome, horizontal rate from the 180° pairs

**Decision.** Visit four positions twice in mirror order. Fit bias, linear drift and one effect per position. Take the horizontal Earth rate only from the 180° pairs.

**Why.**
- A gyro's error can depend on gravity (g-sensitivity). Flipping the IMU reverses gravity in its frame at the same moment as it reverses the Earth's signal, so in a single pass the two are indistinguishable.
- Within a 180° pair about the vertical, gravity stays on the same axis, so g-sensitivity is identical and cancels while the Earth's horizontal component reverses.
- The mirror order makes a linear drift orthogonal to the position effects.

**Rejected.** The v0.1 single pass, whose horizontal estimate was inflated and could drift. Calling the vertical result an Earth-rate measurement, because it is aliased with g-sensitivity and is reported as such.

**Evidence.** With g-sensitivity up to 40 °/h per g, the horizontal rate is unchanged: 11.68 ± 1.15 against 11.44 predicted for a rotating globe, and 0.00 ± 1.37 for the disc. The vertical rate is off by about 40 °/h, as physics requires (EVIDENCE §3; `test_horizontal_ground_rate_is_immune_to_g_sensitivity`).

## 6. The vertical channel can't separate a constant rotation from bias

**Statement.** A constant rotation about the plumb line lies along gravity, as do g-sensitivity and bias on the upward IMU axis. No stationary test and no level flight can tell them apart.

**Consequences.**
- The spinning disc is defined but not tested: it is indistinguishable from the still disc with this protocol.
- The ground vertical rate is fitted across latitudes with one intercept per IMU unit.
- The disc's vertical term is identified only through changes in dλ/dt along the route.

## 7. Residual bias per gravity orientation, and a wide prior

**Decision.**
- The in-flight residual bias gets one free vector per gravity orientation.
- Its prior also covers vibration rectification (5 °/h) and g-sensitivity (5 °/h), which ground calibration can't see.
- The analysis reports how far k moves when the prior is tripled. The same is done for the crab and temperature priors, and `prior_dominated` covers all three.

**Why.** The engines' vibration and the IMU's attitude in flight produce constant offsets that ground calibration misses. A tight prior would push them into k. Flipping the IMU changes the g-sensitivity offset, so a shared bias across a flip would create fake signal.

**Rejected.** The v0.1 prior, which was only the pre/post change with a 1 °/h floor.

**Guarded by.** The `prior_dominated` flag, and the exclusion of such sessions from pooled results.

## 8. Identifiability is measured, not assumed, term by term

**Decision.**
- For each term, report how much of its signal the nuisance terms together could mimic, with no priors: residual bias per gravity orientation, the temperature coefficients and the crab offsets. A session is flagged when this exceeds 0.95: `k_not_identified` for curvature, `k_rot_not_identified`, and `k_disc_not_identified`. The bias-only value is still reported.
- Trade-offs between the k terms themselves aren't counted here. They are carried by the joint covariance of k (section 15).
- The primary pooled result requires curvature to be identified.
- Each term is pooled only from sessions where that term was identified. For example, the disc term comes only from flights whose east velocity changed enough to separate it from bias.

**Why.** On a straight leg, the predicted signal sits on fixed IMU axes, exactly like a bias. A fit can then produce a k with error bars that come entirely from the prior. Bias isn't the only such nuisance: crab and temperature can mimic a term too, so being "identified" against bias alone wasn't enough (third review).

**Headline.** Globe curvature comes first. Globe rotation is shown next to the ground horizontal result. The disc term is reported from heading-diverse sessions only.

**Evidence** (EVIDENCE §2, §8):

| route | curvature identified? | curvature uncertainty |
|---|---|---|
| north, east, south | yes | ±0.94 |
| zigzag | no | |
| straight | no | ±1.06 |
| straight, with IMU turned about the vertical | yes | ±0.17 |
| straight, with IMU flipped | no | ±0.76 |
| 5-h single-heading cruise | no | ±0.80 |
| 5-h cruise with hourly turns | yes | ±0.29 |

## 9. Turning the IMU in flight: same side up

**Decision.** The app reminds the participant to turn the IMU to face the opposite way, keeping the same side up. The gyro integrates each turn, to within 0.1° (EVIDENCE §10), and the analysis maps every mount epoch into one frame. Flips are allowed but discouraged.

**Why.** A turn about the vertical moves the horizontal signal onto other IMU axes while bias and g-sensitivity stay put, which breaks the bias degeneracy. A flip moves gravity to another axis and so brings a new g-sensitivity offset, which teaches nothing.

**Evidence.** EVIDENCE §2 and §8; `test_turns_about_the_vertical_make_a_straight_flight_decisive`, `test_single_heading_airliner_needs_turns_of_the_imu`.

## 10. Model tests: honest χ², calibrated by bootstrap, threshold nominal

**Decision.**
- Test each model against the free fit, using χ² with 3 degrees of freedom, and reject at p < 0.0027: the **nominal** 3σ threshold.
- Two corrections for correlated noise, and the more conservative wins:
  - χ² scaled by the lag-1 autocorrelation of the bin residuals, taken per gyro axis (the largest), since averaging the axes can cancel axis-specific correlation;
  - a bootstrap calibration. Simulate each model's null as its fitted values plus block-resampled free-fit residuals (blocks up to 30 min, for hour-scale bias wander), refit, and measure how far the mean Δχ² exceeds its degrees of freedom. The observed Δχ² is divided by that excess.
- Relative likelihoods are reported but labelled as not probabilities.
- A simulation-calibrated systematic floor of 0.02 is added in quadrature to the globe-rotation uncertainty. See "Evidence".

**Why a calibrated bootstrap rather than a bootstrap p.** Resolving p = 0.0027 directly would need thousands of refits per flight. The calibration needs about a hundred per model.

**What "3σ" does and doesn't claim.** The calibration corrects the mean of Δχ², then assumes a rescaled χ² has the right tail. That assumption isn't demonstrated. The coverage study's 0 false rejections in 90 flights bound the false-rejection rate below 4.0 % (two-sided 95 % Clopper–Pearson; 3.3 % one-sided), not 0.27 %. So per-flight rejections use the nominal threshold. Before any significance is published, `python analysis/tests/coverage.py --null N` must measure the tail directly with thousands of simulated flights, preferably with noise processes taken from long real-device captures. That is an offline job of roughly 10 s per flight per core.

For the true model the calibration factor comes out at 1.0, so honest tests aren't weakened. For wrong models it is often above 1, from prior shrinkage of their nuisance terms. That only makes rejection more cautious.

**Rejected.** v0.1's "Δχ² > 9 = 3σ" (wrong for a multi-parameter comparison), its unscaled χ², its summed Δχ² across sessions, and its best-model vote counts.

**Evidence.**
- In every hard scenario the true model is never rejected (EVIDENCE §7; `test_hardware_faults_never_make_it_confidently_wrong`, `test_adverse_conditions_still_recover_truth`).
- Coverage study (`python analysis/tests/coverage.py`; about 15 min): 90 flights, 30 seeds × 3 truths, every hardware fault at once, north-east-south route.
  - The true model was rejected in 0 of 90 (two-sided 95 % Clopper–Pearson upper bound 4.0 %; rerun on v0.4 with the same coverage figures).
  - Before the floor, the globe-rotation intervals covered the truth in 92 % of flights, the most precise term being the most exposed to scale and alignment errors. With the floor: 94 %, with the 95th-percentile error at 1.97σ.
  - Curvature and disc intervals covered 100 %, so they are conservative.

## 11. Mount-slip watchdog, with and without a globe-based declination model

**Decision.**
- Measure slow yaw slip with the magnetometer, in two versions: with World Magnetic Model declination, and with none.
- A segment is left out of the gyro fit when the **WMM version** sees slip above 1.5 °/h and 3σ.
- The no-declination version is computed and reported as a cross-check.

**Why.**
- A slow turn of the IMU in its mount goes straight into the vertical channel. In v0.1, an 8 °/h slip turned one truth into another.
- The decision uses only the magnetometer and GPS, never the gyro, and the WMM never enters y. But a selection rule can still be informative: if what it drops correlates with route, heading or longitude, and those drive the model terms, k can shift. So every flight where the WMM version excluded anything is refitted with no exclusions (`fit_no_wmm_exclusion`). If any model's rejection changes, or any k moves by more than 1σ, the session is flagged `wmm_selection_sensitive` and left out of the primary result.
- With under 45° of heading range, the airframe's magnetic field can't be fitted and is set to zero; the result says so.
- The raw magnetometer data is kept, so anyone can test claims about declination.

**Rejected.**
- **"Both versions must agree" (v0.2).** This missed a true 2 °/h slip whenever the route's declination drift ran the other way.
- **"Either version".** The no-declination version reads the real declination change along a route as slip, several °/h on many routes. On the test route it discarded two of three clean segments, and the test then rejected nothing at all.

**Evidence.** True slips of 0, 2, 3 and 8 °/h are measured as about −0.1, 1.9, 2.9 and 7.8 °/h with the WMM. Clean flights lose nothing, and the 2 °/h slip is now excluded. The cross-check reads about 3 °/h higher on the test route (EVIDENCE §6; `test_slip_watchdog_catches_yaw_slip_and_spares_clean_flights`).

## 12. Quantization

**Finding.** At ±2000 °/s, one gyro count is 220 °/h. Noise dithers it, but coarse counts interact with constant offsets: the drift fitted during calibration shifts by up to 9 °/h per hour when g-sensitivity is added. At ±250 °/s the shift is under 1 (EVIDENCE §4).

**Action.**
- The app offers ±250, ±500, ±1000 and ±2000 °/s. It writes the choice to the IMU, reads it back at every connection, and logs the readback.
- The analysis decodes with the range the device reported, not the one requested, so a write the IMU ignored can't rescale the data (`test_decoder_uses_the_range_the_imu_reported`).
- A finer range brings a risk: a quick hand turn can exceed it. Turns are clipped and their integrated angle is wrong, so the analysis flags them and leaves out the data after (`test_fast_turn_beyond_full_scale_is_flagged_and_not_used`). The reminders ask for slow turns of about 5 seconds, which is about 36 °/s.
- Still to do on the bench: confirm the range register, then compare bench captures at each range with `lll bench` (count spread, dither, bias instability).

## 13. Temperature

**Decision.**
- Use the IMU's chip temperature, not the phone battery's.
- Apply a coefficient measured on a drift run when one exists, and fit only the residual. The drift-run fit has a time term next to temperature, b = b₀ + β_T (T − T̄) + β_t t. A run where |corr(T, t)| > 0.9 is marked `bias_temp_confounded` and never used as a prior, since a monotonic warm-up can't tell drift from temperature. The bench protocol asks for at least two warm/cool cycles (BENCH §8).
- Otherwise fit freely, report k without the term too, and flag `temperature_sensitive` if any k moves by more than 1σ.

**Why.** A free temperature coefficient can absorb signal if temperature tracks heading or time in the wrong way.

**Evidence.** The coefficients are recovered within 0.12 °/h/°C, and the residual noise drops from 2.12 to 1.39 °/h (EVIDENCE §5; `test_temperature_term_removes_bias`).

## 14. Quality tiers that measure this experiment, without assuming an answer

**Decision.** Rate each IMU unit by the criteria below. Each session uses the latest tier measured **at or before** its own date, so a later bench test can't re-rate earlier flights. Rate the unit by:
- its Allan deviation at 300 s, the worst axis, from a long still recording. The minimum of the Allan curve is reported but treated as descriptive, because it depends on run length and estimator.
- its repeatability in the **reversal test**: repeated same-face 0°/180° turns on a table. Each pair measures the horizontal ground rate free of g-sensitivity, and the pair-to-pair scatter is the unit's repeatability for the one measurement this experiment rests on.

The thresholds (≤ 3 and ≤ 2 °/h for "qualified") are provisional until real units are measured ([BENCH.md](BENCH.md)). A unit is never rated by whether it reproduces the globe's 15 °/h. The same holds for the hardware check that auto-zero is off: it uses a turntable at an independently known rate, not the Earth (BENCH §2).

The ground horizontal rate is the length of a vector, which piles up above zero under noise. So it is reported with a Rice-likelihood estimate, profile-likelihood 68 % and 95 % intervals that can reach zero, and the p-value of zero rate, never as a symmetric "value ± σ".

**Why.** "The unit recovered the expected Earth rate" would assume which model is true.

**Evidence.**
- With g-sensitivity up to 40 °/h per g, six reversal pairs give 11.1 ± 0.7 °/h against 11.44 for a rotating globe, and 0.0 ± 0.6 for the disc (EVIDENCE §13).
- Tests: `test_reversal_test_measures_horizontal_rate_and_its_repeatability`, `test_unit_quality_tier_uses_instrument_criteria_only`.

## 15. Pooling: sessions → units → population, random effects

**Decision.**
- REML random effects, with modified Hartung–Knapp standard errors and t intervals, first within each IMU unit, then across units, for each term.
- The model tests use the **joint** covariance of the three k. Each flight reports its 3×3 covariance: the fit's correlation scaled to the final σ. These are pooled by precision weighting, with each term's between-session and between-unit τ² on the diagonal and no term variance below its own pooled value. Each model is then tested with χ² = dᵀV⁻¹d, referred to F(p, df) when few units set df. Terms a session didn't identify carry no weight from it.
- Hard gates for the primary result.
- With fewer than three units, the result is labelled "single-unit" or "two-unit" and makes no population claim.
- Breakdowns are consistency checks: groups that disagree are flagged, never averaged away.

**Why.**
- Sessions with one IMU share its quirks, and a fixed-effects average treats every 60-s bin as independent.
- DerSimonian–Laird, used in v0.2, is known to be overconfident with few, heterogeneous members.
- The three k come from the same flights, sharing bias, crab and orientation. v0.3 pooled each term separately and then summed z² as if the terms were independent, which isn't χ² at all when they are correlated (third review). `test_pooled_model_test_uses_the_joint_covariance`.

**Evidence.** With unit offsets beyond the stated errors, the random-effects 95 % intervals cover the truth 91 % of the time with 8 units. Fixed effects cover it 23 % of the time (EVIDENCE §9; `test_hierarchical_pooling_covers_the_truth_when_units_differ`).

## 16. Crab: the aircraft's heading isn't its GNSS course

**Decision.** In a crosswind the fuselage points a few degrees off its ground track. The fit gives each GNSS course leg a heading offset with a 5° Gaussian prior, fitted alternately with the linear fit and then linearized into it, so k's uncertainty includes it. Every model's test refits its own offsets.

**Why.** The IMU's orientation in north-east-down coordinates needs the fuselage heading, not the track. Using the course rotates the globe's horizontal predictions.

On a precise flight (a straight route with three same-side-up turns), an 8° crab made the analysis **reject the true rotating globe**, while a flat truth was untouched. Uncorrected crab therefore biases the experiment against the globe.

**Limits.** On an eastbound leg, the globe's rotation and its curvature both tilt local level about the north axis, so a heading offset trades against how the fit splits them. With 8° of crab the true globe is no longer rejected, but k is still about 2σ off. A wider prior only widens the error bars. Heading diversity on the route removes the trade-off.

**Sensitivity, reported, not gated.** Every flight is refitted with crab priors of 3°, 5°, 10° and 15° (`crab_sensitivity`), and a k that spans more than 1σ is flagged `crab_sensitive`. Flights with a single course leg are flagged `single_heading`. Their individual k_rot and k_curv are read only together, through the joint covariance.

**Rejected: a crab-sweep gate.** It was tried in v0.4 and fails both ways (EVIDENCE §11). With 8° of true crab, k stays biased at k_rot ≈ 0.63 at every prior, a span of only 0.35σ, so the gate would let it through. The clean globe flight moves 1.8σ when the prior widens to 15°, so the gate would exclude it. The sweep measures how much the error bars lean on the prior, not crab bias. Only heading diversity separates crab from the split between globe rotation and curvature.

**Evidence.** EVIDENCE §11; `test_crab_angle_no_longer_rejects_the_true_globe`.

## Third review (v0.4)

An external source-level review of v0.3. What it found, and what changed:

| finding | change |
|---|---|
| The auto-zero bench check needed the stationary IMU to show Earth's rotation: circular | A turntable at an independently known rate (BENCH §2) |
| Pooled model test summed z² across correlated k | Joint covariance, precision-weighted pooling, dᵀV⁻¹d (§15) |
| "3σ" not demonstrated by 90 flights | Called nominal. `coverage.py --null` added. Per-axis ρ, longer blocks (§10) |
| Temperature slope from a monotonic warm-up is confounded with drift | Time term, confounding flag, cycled protocol (§13, BENCH §8) |
| Identifiability measured against bias only | Against bias, temperature and crab together. Crab and temperature priors in the sensitivity check (§8, §7) |
| A missing GNSS course became 0° (north) | Missing or poor courses, and courses disagreeing with the coordinates, are excluded from cruise |
| WMM selection called neutral | A no-exclusion refit and the `wmm_selection_sensitive` gate (§11) |
| Crab on single-heading flights | Crab-prior sweep reported; a gate on it was tried and rejected, since it doesn't detect crab bias (§16) |
| Ground horizontal rate as magnitude ± σ | Rice likelihood intervals and p of zero (§14) |
| Unit tier was the latest ever measured | Tier as of each session (§14) |
| Gzip inside the upload zip was decompressed unbounded | A bounded decompressor, checked at upload and when reading |
| Unpinned dependencies, no CI | Lock files, `environment` (versions and commit) in every result, a CI workflow |

**Checked and not changed.** "MATH.md describes an obsolete phone-based experiment." The repository's MATH.md already described the WT901, three tested models, the disc's −dλ/dt term and the WMM watchdog. The review appears to have read a stale copy. Its one valid point, the "can only drop data" wording, is fixed under §11.

## Open points

- **Bench test of the real devices.** Follow [BENCH.md](BENCH.md): decoding, scale factors, auto-zero (against an imposed known rate), the finest workable ranges, Allan deviation, reversal repeatability, Bluetooth recovery and temperature cycles.
- **Measured false-rejection tail.** Run `coverage.py --null` with thousands of flights, ideally with noise models fitted to long real captures, before any significance is published.
- **Fully multivariate random effects.** τ² is estimated per term and placed on the diagonal. Between-unit correlation of the k offsets isn't modelled.
- **Two IMUs on one flight.** They would be excellent independent checks on sensor-specific systematics, but they share the flight: aircraft motion, GNSS, crab, turbulence and temperature. That needs a schema with a list of IMUs and crossed pooling (flight effect plus unit effect), not two independent flights.
- **Heading-free fit.** A flight with no banked turn at all has no forward axis, so only the vertical channel is used. The IMU's azimuth could instead be fitted as a nuisance parameter. This would need care so it can't favour one model. The current protocol instead asks participants to keep recording through one course change.
- **g-sensitivity along gravity, per unit.** A datasheet bound or a dedicated test would tighten the vertical channel.
- **Crab on single-heading legs.** Still the main unresolved bias for the most precise flights. Requiring heading diversity for the primary result would remove it, at the cost of most airliner routes. A magnetometer-based heading constraint would help, but it needs the declination model, so it would add a globe dependence to the predictions, not just to data selection.
