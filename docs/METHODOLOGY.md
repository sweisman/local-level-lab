# Methodology: decisions and how to check them

This page is for anyone who wants to validate the method rather than take it on trust. Each section states a decision, why it was made, what was rejected, the simulation evidence, and the automated test that guards it.

- [MATH.md](MATH.md) has the equations.
- [EVIDENCE.md](EVIDENCE.md) has every number quoted here. Regenerate it with `python analysis/tests/evidence.py`.
- Run the tests with `pytest analysis/tests server/tests`.

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

**Clock.** Bluetooth only adds delay, so sample times come from a straight-line map of device time onto phone time, fitted to the earliest arrivals.

**Evidence.** Within 5 ms over an hour, under random batching, stalls and a ±120 ppm crystal (`test_clock_map_recovers_sample_times`).

## 3. The disc's own transport term

**Decision.** The flat model includes `ω_disc = (0, 0, −dλ/dt)`. On a pole-centred disc, a constant-bearing eastward track circles the centre.

**Why.** The independent geometric check found the term missing from v0.1, which predicted zero for the disc. At 40°N and 230 m/s eastbound it is 9.7 °/h. Leaving it out made the disc artificially easy to reject.

**Why it is written as dλ/dt.** GNSS east velocity is the coordinate rate converted to metres per second. Dividing by `(R_N + h) cos φ` only undoes that conversion, so no globe geometry enters the disc's prediction and the disc's scale doesn't matter.

**Evidence.** All three tested models agree with geometry to 9 × 10⁻¹² rad/s (EVIDENCE §1; `test_flat_models_match_geometry`, `test_sphere_models_match_geometry`).

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
- The analysis reports how far k moves when the prior is tripled.

**Why.** The engines' vibration and the IMU's attitude in flight produce constant offsets that ground calibration misses. A tight prior would push them into k. Flipping the IMU changes the g-sensitivity offset, so a shared bias across a flip would create fake signal.

**Rejected.** The v0.1 prior, which was only the pre/post change with a 1 °/h floor.

**Guarded by.** The `prior_dominated` flag, and the exclusion of such sessions from pooled results.

## 8. Identifiability is measured, not assumed

**Decision.** For each term, report how much of its signal a constant bias could mimic. Flag `k_not_identified` when this exceeds 0.95 for the globe curvature term. Such sessions don't enter the primary pooled result.

**Why.** On a straight leg, the predicted signal sits on fixed IMU axes, exactly like a bias. A fit can then produce a k with error bars that come entirely from the prior.

**Evidence** (EVIDENCE §2, §8):

| route | curvature identified? | curvature uncertainty |
|---|---|---|
| north, east, south | yes | ±0.98 |
| zigzag | no | |
| straight | no | ±1.03 |
| straight, with IMU turned about the vertical | yes | ±0.15 |
| straight, with IMU flipped | no | ±0.74 |
| 5-h single-heading cruise | no | ±0.78 |
| 5-h cruise with hourly turns | yes | ±0.22 |

## 9. Turning the IMU in flight: same side up

**Decision.** The app reminds the participant to turn the IMU to face the opposite way, keeping the same side up. The gyro integrates each turn, to within 0.1° (EVIDENCE §10), and the analysis maps every mount epoch into one frame. Flips are allowed but discouraged.

**Why.** A turn about the vertical moves the horizontal signal onto other IMU axes while bias and g-sensitivity stay put, which breaks the bias degeneracy. A flip moves gravity to another axis and so brings a new g-sensitivity offset, which teaches nothing.

**Evidence.** EVIDENCE §2 and §8; `test_turns_about_the_vertical_make_a_straight_flight_decisive`, `test_single_heading_airliner_needs_turns_of_the_imu`.

## 10. Model tests: honest χ²

**Decision.**
- Test each model against the free fit, using χ² with 3 degrees of freedom.
- Scale χ² for correlation between neighbouring bins, and reject at p < 0.0027.
- Report bootstrap ranges, and label likelihood ratios as not probabilities.

**Rejected.** v0.1's "Δχ² > 9 = 3σ" (wrong for a multi-parameter comparison), its unscaled χ², its summed Δχ² across sessions, and its best-model vote counts.

**Evidence.** In every hard scenario the true model is never rejected (EVIDENCE §7; `test_hardware_faults_never_make_it_confidently_wrong`, `test_adverse_conditions_still_recover_truth`). The hard scenarios cover nonlinear and lagging temperature dependence, a bias jump, scale and misalignment errors, vibration rectification, a Bluetooth dropout, g-sensitivity, turbulence, tilt slip, climb and descent, and GNSS gaps.

## 11. Mount-slip watchdog, with and without a globe-based declination model

**Decision.**
- Measure slow yaw slip with the magnetometer.
- Run the watchdog twice, with World Magnetic Model declination and with none.
- Exclude a segment only when both see slip above 2 °/h. Report both.

**Why.**
- A slow turn of the IMU in its mount goes straight into the vertical channel. In v0.1, an 8 °/h slip turned one truth into another.
- The WMM is built on a globe, so a watchdog that relied on it alone could be accused of favouring the globe.
- Requiring both versions is conservative, and the gyro fit never uses the magnetometer.
- The raw magnetometer data is kept, so anyone can test claims about declination.

**Evidence.** Slips of 0, 2, 3 and 8 °/h are measured as about −0.1, 1.9, 2.9 and 7.8 °/h with the WMM. The version without a declination model reads about 3 °/h higher on the test route, which is the real declination change along it (EVIDENCE §6; `test_slip_watchdog_catches_yaw_slip_and_spares_clean_flights`).

## 12. Quantization

**Finding.** At ±2000 °/s, one gyro count is 220 °/h. Noise dithers it, but coarse counts interact with constant offsets: the drift fitted during calibration shifts by up to 9 °/h per hour when g-sensitivity is added. At ±250 °/s the shift is under 1 (EVIDENCE §4).

**Action.** Bench-test whether the device's gyro range can be lowered, and use the finest range that never saturates in flight.

## 13. Temperature

**Decision.**
- Use the IMU's chip temperature, not the phone battery's.
- Apply a coefficient measured on a drift run when one exists, and fit only the residual.
- Otherwise fit freely, report k without the term too, and flag `temperature_sensitive` if any k moves by more than 1σ.

**Why.** A free temperature coefficient can absorb signal if temperature tracks heading or time in the wrong way.

**Evidence.** The coefficients are recovered within 0.12 °/h/°C, and the residual noise drops from 2.12 to 1.39 °/h (EVIDENCE §5; `test_temperature_term_removes_bias`).

## 14. Quality tiers that don't assume an answer

**Decision.** Rate each IMU unit by bias instability and by the precision of its horizontal ground measurement. Never rate it by whether it reproduces the globe's 15 °/h.

**Why.** "The unit recovered the expected Earth rate" would assume which model is true.

**Guarded by.** `test_unit_quality_tier_uses_instrument_criteria_only`.

## 15. Pooling: sessions → units → population, random effects

**Decision.** DerSimonian–Laird random effects within units, then across units, with hard gates for the primary result. Breakdowns are consistency checks: groups that disagree are flagged, never averaged away.

**Why.** Sessions with one IMU share its quirks, and a fixed-effects average treats every 60-s bin as independent.

**Evidence.** With unit offsets beyond the stated errors, random-effects 95 % intervals cover the truth 90 % of the time. Fixed effects cover it 23 % of the time (EVIDENCE §9; `test_hierarchical_pooling_covers_the_truth_when_units_differ`).

## Open points

- **Bench test of the real devices:** decoding, scale factors, auto-zero polarity, the gyro range, noise and bias stability.
- **Heading-free fit.** A flight with no banked turn at all has no forward axis, so only the vertical channel is used. The IMU's azimuth could instead be fitted as a nuisance parameter. This would need care so it can't favour one model. The current protocol instead asks participants to keep recording through one course change.
- **g-sensitivity along gravity per unit:** a datasheet bound or a dedicated test would tighten the vertical channel.
