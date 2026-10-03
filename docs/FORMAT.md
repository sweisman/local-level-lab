# Session file format (schema_version 2)

A session is one `.zip` file. It's the contract between the Android app, the upload server and the analysis package. Everything in it is released under **CC0-1.0**.

Schema 2 replaces the phone's own motion sensors with an external WitMotion WT901 IMU. No schema 1 data was ever collected, so the analysis reads schema 2 only.

## What "raw" means here

- **`imu.bin.gz` holds the IMU's byte stream exactly as Bluetooth delivered it.** Every read is stored verbatim with the phone's arrival time. Nothing is parsed, filtered, decimated, fused, resampled or bias-corrected on the phone. The analysis decodes it (`analysis/lll/witmotion.py`), so the decoding can be audited and rerun.
- **The data is the least-processed the device exposes, not raw silicon output.** WitMotion's firmware sits between the sensor chip and Bluetooth. It applies the factory bias and scale calibration and a digital low-pass filter. It can also zero the gyro automatically when it thinks the IMU is still, and the app switches that off. The app reads every setting back at each connection and logs it as an `imu_config` event.
- **The device's own attitude outputs are not used.** Its Kalman-filtered angles (0x53) and quaternions (0x59) are switched off.
- **Magnetometer data is kept in full**, in the same byte stream.
- **Display values are never stored.** The live screen's predictions and rough measurements exist only on screen.

## Clock

Every record and row carries a time on Android's `elapsedRealtimeNanos` clock, which is monotonic and keeps counting through sleep.

- **IMU reads:** the arrival time on the phone. The IMU samples on its own crystal. The analysis maps device time onto the phone clock per connection run, with a straight-line fit corrected to the earliest arrivals, because Bluetooth only ever delays. This removes crystal rate error and link jitter, to within a few milliseconds in simulation.
- **GNSS:** `Location.getElapsedRealtimeNanos()`.
- **UTC:** `manifest.clock` maps the session clock to UTC.

## Files

| file | content |
|---|---|
| `manifest.json` | see below |
| `imu.bin.gz` | records `[int64 arrival_ns][uint16 length][bytes]`, little-endian, one per Bluetooth read. One gzip member is appended per recording phase. A truncated last record (app killed mid-write) is ignored. |
| `gnss.csv.gz` | `t_ns,utc_ms,lat,lon,alt_m,speed_mps,bearing_deg,h_acc_m,v_acc_m,speed_acc_mps,bearing_acc_deg,sats_used`. An empty field means not available. GNSS is recorded only during `placement_check` and `flight`. |
| `events.csv.gz` | `t_ns,kind,detail`. See the event list below. |

CSV files are gzip with one header row. They can be multi-member gzip (one member per phase), and standard readers handle that.

### IMU byte protocols

The two device variants use WitMotion's published protocols. Scale factors use the configured full scale, ±2000 °/s and ±16 g by default.

| variant | link | packets used |
|---|---|---|
| `spp` (ICM-42605 + MMC3630) | Bluetooth 2.0 serial | 11 bytes: `55 <type> 8 data bytes <checksum>`. 0x50 device clock, 0x51 accel + chip temperature, 0x52 gyro + battery voltage, 0x54 magnetometer, 0x5F register readback. The checksum is the low byte of the sum of the first 10 bytes. |
| `ble` (MPU9250) | Bluetooth LE 5.0 | 20-byte notifications: `55 61` accel, gyro and angle (angle ignored); `55 71` register readback. The app polls 0x3A once a second, which returns the magnetometer and the chip temperature. No checksum. |

Hand-built example packets with their decoded values are in `docs/test_vectors.json`. Python and Kotlin are both tested against them. Register meanings are unverified until a real device has been checked on the bench.

Decoded streams use the IMU's axes, in SI units: gyro rad/s, accel m/s², magnetometer raw counts, temperature °C.

## manifest.json

```json
{
  "schema_version": 2,
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
    "config": {"rate_hz": 100, "gyro_range_dps": 2000, "accel_range_g": 16, "auto_zero": false, "packets": ["0x50", "0x51", "0x52", "0x54"]}
  },
  "clock": {"elapsed_ns": 0, "utc_ms": 0},
  "flight": {"airline": "", "flight_number": "", "date": "YYYY-MM-DD", "origin": "", "destination": "",
             "aircraft_type": "", "seat": "23A", "seat_position": "window | middle | aisle", "notes": ""},
  "mount": {"type": "window | sidewall | seat_frame | tray | bench | other", "orientation_note": "", "rotated_180_control": false},
  "privacy": {"cal_lat_deg": 40.5},
  "phases": [{"name": "cal_pre.up0", "start_ns": 0, "end_ns": 0, "still_s": 180.0}],
  "quality": {"cal_pre": true, "cal_post": true, "placement_check": true, "flags": []}
}
```

`device` is the phone, which supplies GNSS. `privacy.cal_lat_deg` is the calibration latitude rounded to 0.5°, or `null` if the participant opted out.

### Phase names

| name | meaning |
|---|---|
| `cal_pre.up0`, `.up180`, `.down0`, `.down180`, `.down0.b`, `.up180.b`, `.up0.b` | Ground calibration as a palindrome: each position twice in mirror order. `down180` is one double-length stay. `.b` marks the second visit. Label up or down, turned 180° about the vertical between pairs. |
| `drift_pre`, `drift_post` | optional long stationary recordings |
| `bench` | stationary recording in a bench session |
| `placement_check` | IMU mounted in the aircraft, stillness verified |
| `flight` | main recording |
| `cal_post.*` | the same calibration after the flight |

`still_s` is how many seconds of the phase passed the stillness gate. Sessions with only the four first visits (no `.b`) are still analysed, but without a drift fit.

### Events

| kind | detail |
|---|---|
| `phase_start`, `phase_resume`, `phase_stop` | the phase; `phase_resume` follows an automatic service restart |
| `imu_connect`, `imu_disconnect` | link state |
| `imu_config`, `imu_config_write` | register readback and whether it matched; writes |
| `index_turn` | the participant confirmed a deliberate turn of the IMU: `plane180` (same side up, facing the opposite way) or `flip` |
| `index_skip` | a turn reminder was skipped |
| `placement_shift` | bumped or moved (user-reported, or a tilt change over 2° detected in cruise) |
| `gnss_provider` | GNSS enabled or disabled |
