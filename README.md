# Local Level Lab

A crowdsourced, fully open experiment that tests the shape and motion of the Earth with the motion sensors in ordinary phones, carried on ordinary flights.

A gyroscope measures angular velocity relative to inertial space, not relative to the ground. If the Earth rotates, a phone resting on it turns with it at up to 15.04 °/h. If the Earth is curved, the local-level frame of a moving aircraft (its local horizontal) rotates relative to inertial space, at a rate set by the aircraft's velocity and the Earth's radius: v / R ≈ 8.1 °/h at 900 km/h (250 m/s). The app records raw sensor data. The analysis compares it, side by side, against four models with predictions taken from GPS alone:

| | still | rotating |
|---|---|---|
| **flat** | no rotation | 15.04 °/h about the disc normal (local vertical), everywhere |
| **sphere** | transport rate only | Earth rate (latitude-dependent) + transport rate |

Sensor resolution isn't the problem; bias stability is. A single phone's gyro drift is comparable to these signals, so the design depends on careful calibration, long stable recordings, turns, controls, and **pooling many flights**.

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
lll synth hard.zip --truth flat_still --adverse   # temperature drift, turbulence, mount slip, climb/descent, GNSS gaps
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

Environment variables: `LLL_DATA`, `LLL_MAX_UPLOAD_MB` (default 200), `LLL_MAX_UNCOMPRESSED_MB` (default 2000, declared size of the zip's contents), `LLL_UPLOADS_PER_HOUR` (default 20, per client IP and per install ID).

The per-IP limit uses the client address uvicorn sees. Behind a reverse proxy on the same host, make sure it sends `X-Forwarded-For` (Caddy does by default; nginx needs `proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;`), otherwise every upload shares one bucket.

## Android

Open `android/` in Android Studio, or run `./gradlew assembleDebug` (JDK 17 or 21, Android SDK 35). To set the default upload server for your build, use `lll.serverUrl` in `android/gradle.properties`. Users can change it in Settings.

## Openness

- Code: **AGPL-3.0-or-later** © Scott Weisman.
- Data: **CC0** ([DATA_LICENSE.md](DATA_LICENSE.md)).
- What's collected: [PRIVACY.md](PRIVACY.md).
- No analytics, ads or proprietary SDKs.

Reviews and criticism are welcome: [CONTRIBUTING.md](CONTRIBUTING.md).
