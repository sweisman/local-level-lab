# Session file format (schema_version 1)

A session is one `.zip` file. It's the contract between the Android app, the upload server and the analysis package. Everything in it is released under **CC0-1.0**.

## Raw-data guarantee

- Every sensor sample is written exactly as Android delivers it. Nothing is filtered, decimated, fused, re-sampled or bias-corrected on the device.
- Floats are written with the shortest decimal text that round-trips the original 32-bit value, so reading a value back and casting it to float32 gives exactly the bits the OS delivered.
- The `*_uncal` streams are the primary data. The OS-calibrated streams (`gyro`, `accel`) and `game_rv` are logged too, but only for comparison.
- The live screen's predictions and rough measurements are for display only. They are never written to the session.

## Clock

Every row in every stream starts with `t_ns`. That's Android's `elapsedRealtimeNanos` clock: `SensorEvent.timestamp` for sensors, `Location.getElapsedRealtimeNanos()` for GNSS. One monotonic clock means every stream lines up with no guessing. `manifest.clock` maps that clock to UTC.

## Files

| file | columns | units |
|---|---|---|
| `manifest.json` | see below | |
| `gyro_uncal.csv.gz` | `t_ns,x,y,z,bx,by,bz` | rad/s. `x,y,z` are raw with no drift compensation. `b*` is the OS's own bias estimate, recorded but not applied |
| `gyro.csv.gz` | `t_ns,x,y,z` | rad/s (OS-calibrated) |
| `accel_uncal.csv.gz` | `t_ns,x,y,z,bx,by,bz` | m/s² |
| `accel.csv.gz` | `t_ns,x,y,z` | m/s² |
| `mag_uncal.csv.gz` | `t_ns,x,y,z,bx,by,bz` | µT |
| `pressure.csv.gz` | `t_ns,hpa` | hPa |
| `game_rv.csv.gz` | `t_ns,x,y,z,w` | unit quaternion |
| `gnss.csv.gz` | `t_ns,utc_ms,lat,lon,alt_m,speed_mps,bearing_deg,h_acc_m,v_acc_m,speed_acc_mps,bearing_acc_deg,sats_used` | an empty field means not available |
| `battery.csv.gz` | `t_ns,temp_c,level_pct,plugged` | about every 10 s. Battery temperature stands in for sensor temperature |
| `events.csv.gz` | `t_ns,kind,detail` | phase start/stop, screen on/off, sensor accuracy changes, placement-shift warnings, notes |

The sensor axes are Android's device frame: x points right, y points up along the screen, and z points out of the screen. At rest, the accelerometer reads about +9.81 m/s² along whichever axis points **up**.

A stream's file may be missing if the device doesn't have that sensor. Each file is a gzip CSV with one header row. It may be a multi-member gzip, because the app appends one member per recording phase, and standard gzip readers handle that.

## manifest.json

```json
{
  "schema_version": 1,
  "data_license": "CC0-1.0",
  "session_id": "uuid",
  "install_id": "uuid (random per install, no link to identity)",
  "created_utc": "2026-10-02T13:00:00Z",
  "app": {"name": "Local Level Lab", "version": "0.1.0", "build": 1},
  "device": {"manufacturer": "...", "model": "...", "android_sdk": 35, "android_release": "15"},
  "sensors": {"gyro_uncal": {"name": "...", "vendor": "...", "version": 1, "resolution": 0.0, "max_range": 0.0, "min_delay_us": 0, "fifo_max": 0}},
  "sampling_period_us": 10000,
  "clock": {"elapsed_ns": 0, "utc_ms": 0},
  "flight": {"airline": "", "flight_number": "", "date": "YYYY-MM-DD", "origin": "", "destination": "",
             "aircraft_type": "", "seat": "window|middle|aisle", "row": "", "notes": ""},
  "mount": {"type": "window|sidewall|tray|seat_frame|handheld|other", "orientation_note": "", "rotated_180_control": false},
  "privacy": {"cal_lat_deg": 40.5},
  "phases": [
    {"name": "cal_pre.up0", "start_ns": 0, "end_ns": 0, "still_s": 300.0}
  ],
  "quality": {"cal_pre": true, "cal_post": true, "placement_check": true, "flags": []}
}
```

### Phase names

| name | meaning |
|---|---|
| `cal_pre.up0`, `cal_pre.up180`, `cal_pre.down0`, `cal_pre.down180` | 4-position stationary calibration before the flight (face up, then turned 180° about vertical, then face down, then face down turned 180°) |
| `drift_pre` | optional long stationary recording before the flight |
| `placement_check` | phone mounted in the aircraft, stillness verified |
| `flight` | main recording |
| `cal_post.*`, `drift_post` | the same again after the flight |

`still_s` is how many seconds of the phase passed the stillness gate. `privacy.cal_lat_deg` is the calibration latitude rounded to 0.5°, or `null` if the user opted out. No GNSS rows are written during `cal_*` or `drift_*` phases.
