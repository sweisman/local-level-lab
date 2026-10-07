# Bench validation

Before a flight can enter the provisional primary corpus, a curator must approve the complete bench evidence using the [registry workflow](CURATION.md). A quality tier calculated from a flight is not a bench certificate; approval must precede the flight.

No flight result means anything until the real IMUs pass these checks. They come from the adversarial reviews and from the open points in [METHODOLOGY_TECHNICAL.md](METHODOLOGY_TECHNICAL.md).

Each step lists what to do, the `lll bench` output to read, and the pass criterion.

- **Recording:** in the app, Settings → Bench tests → New bench session. It has a palindrome calibration, a reversal test and a long still recording.
- **Reading:** `lll bench session.zip` prints the numbers below. `lll bench a.zip b.zip` compares two sessions.

Thresholds marked *provisional* will be revised once real units have been measured. Record every result, pass or fail, so the thresholds can be set from data.

## 1. The stream decodes and the settings stick

1. **Pair and configure.** Pair the IMU, choose it in Settings, and tap "Write and verify IMU settings". Pass if the Settings screen shows "Settings verified: yes".
2. **Record.** Make a short bench session, 10 minutes still.
3. **Check the decode.** `lll bench s.zip`:
   - `decode.bad_checksums` and `decode.unparsed_bytes` are near 0, and the serial variant shows `0x52` gyro packets.
   - `config_readbacks` contains the values the app wrote.
   - `decode.gyro_range_used_dps` equals the range you chose.
   - `rate_hz` matches the configured rate within 1 %.
   - `samples_received` is within 0.1 % of `samples_expected`.
4. **Scale factors.** Lying still and level, the accelerometer's vertical axis reads 9.81 m/s² within 1 %. Turn the IMU 90° by hand about one axis; the integrated gyro should give 90° within 1°. A wrong full scale shows up here immediately.

## 2. Automatic gyro zeroing is really off

This is the most important single check. If the firmware zeros the gyro while it's still, it erases any slow steady rotation, including the transport rate during smooth cruise.

The check must not rely on the Earth's rotation. Requiring the stationary IMU to show Ω|cos φ| would certify the instrument only if the globe rotates, before the experiment has asked. So the test imposes a slow rotation whose rate is known independently, from the apparatus alone.

**Apparatus.** Anything that turns the IMU steadily about one axis at a slow rate (roughly 10–30 °/h) known without reference to the Earth. Examples: a geared or stepper turntable whose total angle over the run is read off a scale, or a clock movement. Run it once clockwise and once anticlockwise at the same rate. Half the difference between the two mean rates about the turntable axis is the imposed rate. The gyro bias and any Earth rate cancel, so nothing model-dependent remains.

1. **Off run.** Switch "auto-zero ON" **off**. Make two bench sessions on the turntable, clockwise and anticlockwise.
2. **On run.** Switch "auto-zero ON" **on**. Repeat both directions, then switch it off again. Flights always force it off regardless.
3. **Read.** `lll bench` on each session gives `gyro_mean_dph` per axis. For each setting, take half of (clockwise − anticlockwise) on the turntable axis.

**Pass:**
- With auto-zero **off**, that half-difference equals the imposed rate within its error, and within 1 °/h for a rate of 10 °/h or more.
- With auto-zero **on**, it is clearly suppressed or distorted.

If both settings preserve the imposed rate, the test can't tell whether the register works. Use a slower rate, inside the firmware's zeroing window. If both suppress it, or the off run does, the register or its polarity is wrong. Stop and fix `WitConfig` before anything else.

The stationary horizontal rate (`reversal_h_dph`, `calibration_h_dph`) is recorded too, but it is a measurement, never a pass criterion here.

## 3. Quantization and the gyro range

1. **One session per range.** Make bench sessions at ±2000, ±500 and ±250 °/s. Settings → Gyro range, then "Write and verify".
2. **Compare.** `lll bench r2000.zip r250.zip`.

**Pass:**
- `gyro_lsb_dph` shrinks with the range: 220, 55, then 27 °/h.
- `gyro_sd_lsb` is at least about 0.5 counts, so noise dithers the counts.
- `gyro_mode_fraction` is clearly below 1.
- Allan deviation at 300 s doesn't get worse at the finer range.

Use the finest range that passes. Before trusting it, turn the IMU by hand at your normal speed: `gyro_saturated_samples` must stay 0. Then repeat step 1 with the accelerometer at ±4 g.

## 4. Stability

1. **Long still run.** Bench recording of 2 hours or more, untouched, ideally at a stable room temperature.
2. **Read.** `adev_at_dph` at 60, 300, 900 and 1800 s, per axis. `bias_instability_dph` is descriptive only.

**Provisional pass:** at 300 s, ≤ 3 °/h on every axis for "qualified", or ≤ 6 °/h for "usable". The analysis's tiers use the same numbers.

**Research persistence diagnostic.** See [input persistence](INPUT_PERSISTENCE.md) for
`analysis/tests/characterize_input_persistence.py`. It processes every explicit `bench`,
`drift_pre` and `drift_post` phase separately. IMU second means require at least80%
sample coverage, endpoint coverage and no internal gap exceeding3sample periods;
nonfinite/saturated seconds are rejected. GPS is optional and never interpolated.
Separate IMU, GPS and simultaneous11-channel summaries retain cross covariance,
within-contiguous-run lag moments at0/1/5/15/60/300s and nonoverlapping block-mean SD
at1/15/60/300s. Mean-only and linear-detrended views are both retained, with temperature
range and reported GPS accuracy scales. Raw units and valid pair/block counts are explicit.
Zero-variance correlations are null; fewer than3complete seconds is insufficient.
Finite-sample normalized lag moments can exceed1 and are not a positive-definite kernel.
No exponential-time fit, measured-error bound, qualification threshold or policy promotion
is inferred. Stationary covariance includes environmental/drift effects and cannot
substitute for airborne GPS or motion-correction controls. Nine controlled software
tests pass; no actual hardware measurement has been run.

## 5. The measurement that matters: repeated reversals

1. **Reversal test.** Run it: twelve placements, label up, turning 180° between each.
2. **Repeat.** Do it on at least three different days.
3. **Read.** `reversal.h_dph` gives each pair, plus `reversal.h_mean_dph` and `reversal.h_sd_dph`.

**Pass:**
- The measured horizontal rate is consistent across days and units within stated uncertainty; agreement with a preferred Earth model is not an instrument qualification criterion.
- The day-to-day spread is within the stated errors.

*Provisional:* `h_sd_dph` ≤ 2 °/h for "qualified".

**Two units side by side.** Run their reversal tests on the same table at the same time. Agreement between two independent instruments is the strongest check this experiment can get on the ground.

## 6. Ground calibration

**Do:** the full palindrome calibration, repeated on different days.

**Pass:**
- `calibration.earth_h_dph` agrees with the reversal test.
- `calibration.drift_dph_per_h` stays small.
- The vertical `earth_up_dph` is reported as aliased with g-sensitivity. Its spread between days shows how stable that g-sensitivity is.

## 7. Bluetooth

1. **Drop the link.** During a bench recording, tap "Disconnect test" a few times.
2. **Check recovery.** In `lll bench`:
   - `arrival_ms.gaps_over_1s` counts the drops;
   - the decode starts a new run after each;
   - no samples are timed out of order.
3. **BLE loss.** For the BLE unit, `decode.loss_estimate` and `decode.samples_lost_detected` show notification loss.
4. **Distance.** Repeat at the distance the phone will be from the IMU in a cabin, typically 0.5–1 m.

**Pass:**
- Every drop recovers automatically.
- `analyze` doesn't flag `imu_link_gaps` outside the drops you made.
- BLE loss stays under 0.1 %.

## 8. Temperature

**Do:** a long still recording while the IMU warms and cools by 5–10 °C **at least twice**. For example, two cycles of slow warming then slow cooling over several hours. Don't heat it quickly.

**Why cycles.** In a single warm-up, temperature rises with time, so ordinary bias drift looks exactly like a temperature coefficient. The analysis fits bias = b₀ + β_T (T − T̄) + β_t t, and it can separate β_T from drift only when temperature isn't a straight function of time.

**Read:** `bias_vs_temp.slope_dph_per_c` with its `slope_sd_dph_per_c`, `drift_dph_per_h`, `temp_time_corr` and `confounded`, per axis.

**Pass:** this is not pass or fail; it characterizes the unit.
- If `confounded` is true (|corr(T, t)| > 0.9), the slope is unusable. Repeat with cycles. The flight analysis ignores confounded drift runs when it sets the temperature prior.
- A strong slope that repeats across cycles can be used as the known coefficient.
- Hysteresis, meaning different slopes warming and cooling, means the temperature term can't be trusted. Flights should then be flagged `temperature_sensitive`.

## 9. Before the first flight

Every step above has passed for the unit you'll fly. Then:

- Gyro and accelerometer ranges set to the finest values that pass section 3.
- The defaults in `LllApp.kt` (`imuGyroRangeDps`, `imuAccelRangeG`) updated, if every unit passes.
- The captures committed as test fixtures under `analysis/tests/fixtures/`, so the decoder is pinned to real bytes.
- The provisional thresholds in `analysis/lll/analyze.py` revised from the measured units.
