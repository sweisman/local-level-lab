# Local Level Lab

A crowdsourced, fully open experiment that tests the shape and motion of the Earth with the motion sensors in ordinary phones, carried on ordinary flights.

A gyroscope measures rotation relative to the stars. If the Earth rotates, a phone resting on it turns with it at up to 15 °/h. If the Earth is curved, an airliner holding level flight has to keep pitching to follow the surface: about 7 °/h at 900 km/h. The app records raw sensor data. The analysis compares it, side by side, against four models with predictions taken from GPS alone:

| | still | rotating |
|---|---|---|
| **flat** | no rotation | 15 °/h about vertical, everywhere |
| **sphere** | transport rate only | Earth rate (latitude-dependent) + transport rate |

A single phone's gyro drift is comparable to these signals, so the design depends on careful calibration, long stable recordings, turns, controls, and **pooling many flights**.

## Repository

| path | what |
|---|---|
| `android/` | The Android app (Kotlin/Compose). Guided calibration, drift runs, placement check, raw recording, live or battery-saver display, upload/share, in-app instructions |
| `server/` | Upload server (FastAPI + SQLite) that publishes every raw upload as an open dataset |
| `analysis/` | The `lll` Python package. Single-session analysis and HTML report, multi-session collation, and a synthetic-data generator |
| `docs/` | [FORMAT](docs/FORMAT.md) (file spec), [MATH](docs/MATH.md) (models, method, approximations), [PROTOCOL](docs/PROTOCOL.md) (participant steps), shared test vectors |

## Quick start: analysis

```sh
python -m venv .venv && . .venv/bin/activate
pip install -e analysis -e server pytest httpx
lll synth demo.zip --truth sphere_rotating   # or sphere_still / flat_rotating / flat_still
lll analyze demo.zip                         # writes demo.result.json + demo.report.html
lll collate . -o collated                    # pools every *.result.json under .
pytest analysis/tests server/tests
```

## Server

```sh
lll-server --data /srv/lll serve --host 127.0.0.1 --port 8000   # put Caddy/nginx in front for TLS
lll-server --data /srv/lll process        # analyze new uploads → reports
lll-server --data /srv/lll collate        # pooled report at /report
lll-server --data /srv/lll export dump/   # full public dataset + SHA256SUMS
```

Public endpoints:

- `POST /api/v1/sessions` (upload)
- `GET /api/v1/sessions` (index)
- `GET /api/v1/sessions/{id}` (status and results)
- `GET /api/v1/sessions/{id}/raw` (the original zip, byte-identical)
- `GET /api/v1/sessions/{id}/report`
- `GET /report`

Environment variables: `LLL_DATA`, `LLL_MAX_UPLOAD_MB` (default 200), `LLL_UPLOADS_PER_HOUR` (default 20).

## Android

Open `android/` in Android Studio, or run `./gradlew assembleDebug` (JDK 17 or 21, Android SDK 35). To set the default upload server for your build, use `lll.serverUrl` in `android/gradle.properties`. Users can change it in Settings.

## Openness

- Code: **AGPL-3.0-or-later** © Scott Weisman.
- Data: **CC0** ([DATA_LICENSE.md](DATA_LICENSE.md)).
- What's collected: [PRIVACY.md](PRIVACY.md).
- No analytics, ads or proprietary SDKs.

Reviews and criticism are welcome: [CONTRIBUTING.md](CONTRIBUTING.md).
