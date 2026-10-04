# Bench validation

No flight result means anything until the real IMUs pass these checks. They come from the adversarial reviews and from the open points in [METHODOLOGY.md](METHODOLOGY.md).

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

This is the most important single check. If the firmware zeros the gyro while it's still, it erases the Earth's rotation, and the transport rate too during smooth cruise.

1. **Off run.** Bench session with "auto-zero ON" switched **off**: a calibration plus the reversal test.
2. **On run.** Switch "auto-zero ON" **on**. Make a second bench session with the same steps, then switch it off again. Flights always force it off regardless.
3. **Compare.** `lll bench off.zip on.zip`.

**Pass:**
- In the off run, `reversal_h_dph` and `calibration_h_dph` are near Ω|cos φ| at your latitude: 12.8 °/h at 32°N, for example. They are clearly not near 0.
- In the on run they collapse towards 0.

If the two runs look the same, the register or its polarity is wrong. Stop and fix `WitConfig` before anything else.

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

## 5. The measurement that matters: repeated reversals

1. **Reversal test.** Run it: twelve placements, label up, turning 180° between each.
2. **Repeat.** Do it on at least three different days.
3. **Read.** `reversal.h_dph` gives each pair, plus `reversal.h_mean_dph` and `reversal.h_sd_dph`.

**Pass:**
- The mean agrees with Ω|cos φ| at your latitude, or with 0, consistently across days and units.
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

**Do:** a long still recording while the room or the IMU slowly warms or cools by 5–10 °C. For example, start cold and let it warm. Don't heat it quickly.

**Read:** `bias_vs_temp.slope_dph_per_c` and its `correlation`, per axis.

**Pass:** this is not pass or fail; it characterizes the unit. A strong, repeatable slope can be used as the known coefficient. Hysteresis, meaning different slopes warming and cooling, means the temperature term can't be trusted, and flights should be flagged `temperature_sensitive`.

## 9. Before the first flight

Every step above has passed for the unit you'll fly. Then:

- Gyro and accelerometer ranges set to the finest values that pass section 3.
- The defaults in `LllApp.kt` (`imuGyroRangeDps`, `imuAccelRangeG`) updated, if every unit passes.
- The captures committed as test fixtures under `analysis/tests/fixtures/`, so the decoder is pinned to real bytes.
- The provisional thresholds in `analysis/lll/analyze.py` revised from the measured units.
