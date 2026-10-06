# Session file format (schema_version 3; schema 2 readable)

A session is one `.zip` file. It's the contract between the Android app, the upload server and the analysis package. Everything in it is released under **CC0-1.0**.

Schema 2 replaces the phone's own motion sensors with an external WitMotion WT901 IMU. No schema 1 data was ever collected, the analysis reads schemas 2 and 3. Schema 3 removes exact seat from new recordings and stores separate, fresh calibration locations. Historical archives remain unchanged.

## What "raw" means here

- **`imu.bin.gz` holds the IMU's byte stream exactly as Bluetooth delivered it.** Every read is stored verbatim with the phone's arrival time. Nothing is parsed, filtered, decimated, fused, resampled or bias-corrected on the phone. The analysis decodes it (`analysis/lll/witmotion.py`), so the decoding can be audited and rerun.
- **The data is the least-processed the device exposes, not raw silicon output.** WitMotion's firmware sits between the sensor chip and Bluetooth. It applies the factory bias and scale calibration and a digital low-pass filter. It can also zero the gyro automatically when it thinks the IMU is still, and the app switches that off. The app reads every setting back at each connection and logs it as an `imu_config` event.
- **The device's own attitude outputs are not used.** Its Kalman-filtered angles (0x53) and quaternions (0x59) are switched off.
- **Magnetometer data is kept in full**, in the same byte stream.
- **Display values are never stored.** The live screen's predictions and rough measurements exist only on screen.

## Clock

Every record and row carries a time on Android's `elapsedRealtimeNanos` clock, which is monotonic and keeps counting through sleep.

- **IMU reads:** the arrival time on the phone. The IMU samples on its own crystal. The analysis maps device time onto the phone clock per connection run, with a straight-line fit corrected to the earliest arrivals, because Bluetooth only ever delays. This removes crystal rate error and link jitter, to within a few milliseconds in simulation.
  - **BLE:** samples are counted, so lost notifications are found from steps in the earliest-arrival envelope and the sample index is restored. The decode reports `samples_lost_detected` and `loss_estimate`.
  - **Serial:** if the device sends its clock packet less often than its gyro packets, each gyro sample is dated from the nearest preceding clock packet plus whole sample periods.
  - **Never late:** no sample is ever timed later than its own arrival.
- **GNSS:** `Location.getElapsedRealtimeNanos()`.
- **UTC:** `manifest.clock` maps the session clock to UTC.

New flight phases also log `clock_anchor` at start/resume with `elapsed_ns`, `utc_ms`,
`elapsed_after_ns` and `source=phone_wall_clock`. These bracket a phone wall-clock read;
they do not certify UTC accuracy. `gnss_start` records fresh-fix availability, acknowledgment
and resume status. A missing fix does not stop IMU capture or later GNSS logging.

## Files

| file | content |
|---|---|
| `manifest.json` | see below |
| `imu.bin.gz` | records `[int64 arrival_ns][uint16 length][bytes]`, little-endian, one per Bluetooth read. The app writes an uncompressed local journal and compresses it only for packaging. On recovery, an incomplete final journal record is truncated and the session is flagged recording_data_loss. |
| `gnss.csv.gz` | `t_ns,utc_ms,lat,lon,alt_m,speed_mps,bearing_deg,h_acc_m,v_acc_m,speed_acc_mps,bearing_acc_deg,sats_used`. An empty field means not available. GNSS is recorded only during `placement_check` and `flight`. |
| `events.csv.gz` | `t_ns,kind,detail`. See the event list below. |

CSV files are gzip with one header row. They can be multi-member gzip (one member per phase), and standard readers handle that.

### IMU byte protocols

The two device variants use WitMotion's published protocols. Scale factors use the gyro full scale (±250, ±500, ±1000 or ±2000 °/s, chosen in Settings; register 0x20) and ±16 g for the accelerometer.

**Which gyro range is used for decoding.** `imu.config.gyro_range_dps` records the range the app asked for. The app also reads register 0x20 back at every connection and logs it in an `imu_config` event (for example `0x20=0x1`, meaning ±500 °/s). The analysis decodes with the range the device reported, because decoding at the wrong full scale would rescale every rate. It flags `imu_range_differs_from_intended` when the two differ, and `imu_range_inconsistent` when readbacks disagree with each other; in that case it falls back to the intended range. The accelerometer range works the same way: register 0x21 (0 = ±2, 1 = ±4, 2 = ±8, 3 = ±16 g), recorded as `imu.config.accel_range_g`, with flags `imu_accel_range_differs_from_intended` and `imu_accel_range_inconsistent`.

**Saturation.** A gyro count at full scale (±32767) means the rate may have been clipped. The decoder marks such samples, and a deliberate turn of the IMU that clipped is flagged `imu_turn_saturated`. The IMU's orientation after it is then unknown, so the later flight data is left out.

| variant | link | packets used |
|---|---|---|
| `spp` (ICM-42605 + MMC3630) | Bluetooth 2.0 serial | 11 bytes: `55 <type> 8 data bytes <checksum>`. 0x50 device clock, 0x51 accel + chip temperature, 0x52 gyro + battery voltage, 0x54 magnetometer, 0x5F register readback. The checksum is the low byte of the sum of the first 10 bytes. |
| `ble` (MPU9250) | Bluetooth LE 5.0 | 20-byte notifications: `55 61` accel, gyro and angle (angle ignored); `55 71` register readback. The app polls 0x3A once a second, which returns the magnetometer and the chip temperature. No checksum. |

Hand-built example packets with their decoded values are in `docs/test_vectors.json`. Python and Kotlin are both tested against them. Register meanings are unverified until a real device has been checked on the bench.

Decoded streams use the IMU's axes, in SI units: gyro rad/s, accel m/s², magnetometer raw counts, temperature °C.

## manifest.json

```json
{
  "schema_version": 3,
  "data_license": "CC0-1.0",
  "kind": "flight | bench",
  "session_id": "uuid",
  "install_id": "uuid (random per app install)",
  "created_utc": "2026-10-03T13:00:00Z",
  "app": {"name": "Local Level Lab", "version": "…", "build": 1},
  "device": {"manufacturer": "…", "model": "…", "android_sdk": 35, "android_release": "15"},
  "imu": {
    "variant": "spp | ble",
    "model": "…",
    "firmware": "",
    "unit_id": "uuid (random per physical IMU; the Bluetooth address never leaves the phone)",
    "config": {"rate_hz": 100, "gyro_range_dps": 250, "accel_range_g": 16, "auto_zero": false, "packets": ["0x50", "0x51", "0x52", "0x54"]}
  },
  "clock": {"elapsed_ns": 0, "utc_ms": 0},
  "flight": {"airline": "Etihad Airways", "flight_number": "EY10", "date": "2025-09-01", "origin": "ORD", "destination": "AUH",
             "airline_id": "openflights:2222", "airline_iata": "EY", "airline_icao": "ETD",
             "airline_directory_revision": "5d623a6969a1adee7961cf1c9a8a212c4a784713",
             "date_basis": "origin-local", "track_verification": "pending",
             "aircraft_type": "", "seat_position": "unspecified | window | middle | aisle", "notes": ""},
  "mount": {"type": "window | sidewall | seat_frame | tray | bench | other", "orientation_note": "", "rotated_180_control": false},
  "privacy": {"cal_locations": {"cal_pre": {"lat_deg": 40.5, "age_s": 12}, "cal_post": {"lat_deg": 51.5, "age_s": 8}}},
  "bench": {"auto_zero_on": false},
  "phases": [{"name": "cal_pre.up0", "start_ns": 0, "end_ns": 180000000000, "still_s": 180.0}],
  "quality": {"cal_pre": true, "cal_post": true, "placement_check": true, "reversal": false, "flags": []}
}
```

`device` is the phone, which supplies GNSS. `bench` appears only in bench sessions: `auto_zero_on` is true when the session was recorded with the bench-only auto-zero polarity test, which never applies to flights. `privacy.cal_locations` stores each calibration latitude rounded to 0.5° and the fix age (at most 900 seconds). Missing, stale and legacy shared locations are unknown for model comparisons; departure latitude is never reused for arrival. Exact legacy `flight.seat` remains readable. New sessions use optional `seat_position`, default unspecified.

### Flight identity and external tracks

New flight manifests additionally carry `airline_id` (OpenFlights record ID), `airline_iata`,
`airline_icao`, `airline_directory_revision`, `date_basis="origin-local"`, and
`track_verification="pending"`. Airline selection, a matching flight-number prefix, a valid
calendar date, and different three-letter airport codes are required in the app. The date is
the scheduled departure date at the origin, which can differ from a track's first UTC date.
It stays the scheduled date when a delay crosses midnight. The app's default date comes from
the phone and must be confirmed. Numbers are normalized to the carrier's IATA prefix, or ICAO
when IATA is unavailable; bare numbers and matching prefixes are accepted. Shared codes retain
distinct directory IDs, names and ICAO codes. Airport checks cover syntax, not actual existence
or a scheduled route.
These fields identify the intended flight; they do not establish that it operated or that its
track is useful. Historical archives without these optional metadata fields remain readable.

External provider tracks remain separate provenance-bearing artifacts. Do not replace
`gnss.csv.gz`, invent GNSS accuracy/satellite fields, or select a track by gyro/model agreement.
Observed-versus-estimated positions, timestamp basis, coverage and timing/position uncertainty
must be checked before any separately validated analysis can use a fallback.

### Phase names

| name | meaning |
|---|---|
| `cal_pre.up0`, `.up180`, `.down0`, `.down180`, `.down0.b`, `.up180.b`, `.up0.b` | Ground calibration as a palindrome: each position twice in mirror order. `down180` is one double-length stay. `.b` marks the second visit. Label up or down, turned 180° about the vertical between pairs. |
| `drift_pre`, `drift_post` | optional long stationary recordings |
| `bench` | stationary recording in a bench session |
| `rev.up0.N`, `rev.up180.N` | bench reversal test: label up, alternating 0° and 180° about the vertical, N = 1…6 |
| `placement_check` | IMU mounted in the aircraft, stillness verified |
| `flight` | main recording |
| `cal_post.*` | the same calibration after the flight |

`still_s` is how many seconds of the phase passed the stillness gate. Sessions with only the four first visits (no `.b`) are still analysed, but without a drift fit.

### Events

| kind | detail |
|---|---|
| `phase_start`, `phase_resume`, `phase_stop` | the phase; `phase_resume` follows an automatic service restart |
| `clock_anchor` | Flight start/resume: `elapsed_ns`, `utc_ms`, `elapsed_after_ns`, `source=phone_wall_clock`; elapsed timestamps bracket the wall-clock read without certifying UTC accuracy |
| `gnss_start` | Flight start/resume: `fresh_fix`, `acknowledged`, `resume`; acknowledgment is the start request's value, while automatic resume can continue without a fresh fix |
| `imu_connect`, `imu_disconnect` | link state |
| `imu_config`, `imu_config_write` | register readback and whether it matched; writes |
| `index_turn` | the participant confirmed a deliberate turn of the IMU: `plane180` (same side up, facing the opposite way) or `flip` |
| `index_skip` | a turn reminder was skipped |
| `imu_disconnect_test` | the bench "disconnect test" dropped the link on purpose |
| `placement_shift` | bumped or moved (user-reported, or a tilt change over 2° detected in cruise) |
| `gnss_provider` | GNSS enabled or disabled |

Local journals, upload snapshots, recovery markers and local.json are device-only. Recording requires verified configuration; instrument settings are locked during a phase. Raw archives are immutable once uploaded. Provenance and bench certificates are separate server-owned records, never authoritative manifest fields. See [PRIMARY_CORPUS.md](PRIMARY_CORPUS.md).
