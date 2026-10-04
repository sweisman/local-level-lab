# Local Level Lab

A fully open experiment that tests the shape and motion of the Earth with a small motion sensor (an IMU) carried on ordinary flights. It starts with a small number of careful operators; crowdsourcing can follow once the instrument has been characterized.

A gyroscope measures angular velocity relative to inertial space, not relative to the ground. If the Earth rotates, a sensor resting on it turns with it at up to 15.04 °/h. And as an aircraft moves, its local horizontal ("local level") turns relative to inertial space at a rate the Earth's shape sets. On a globe it tilts forward at v / R ≈ 8.1 °/h at 900 km/h. On a flat disc it never tilts, but an eastbound track circles the disc's centre. The IMU records the least-processed data it can deliver. The analysis compares it, side by side, against models whose predictions come from the GPS track alone. Four kinematic models are defined; three can be told apart by this protocol, and those are the ones tested:

| model | Earth rotation | moving over the surface |
|---|---|---|
| **globe, rotating** | 15.04 °/h about the Earth's axis (latitude-dependent split between vertical and horizontal) | local level tilts towards the direction of travel, and turns slowly about the vertical |
| **globe, still** | none | as above |
| **flat disc, still** | none | local level never tilts; it turns about the vertical once per 360° of longitude |
| *flat disc, spinning* (not tested) | 15.04 °/h about the vertical, everywhere | as above |

A spinning disc differs from a still one only by a constant rotation about the vertical, which no stationary test and no level flight can separate from the gyro's own bias along gravity. So the two disc models make the same testable predictions, and the still disc stands for both. Details: [MATH.md](docs/MATH.md#the-models-four-defined-three-tested).

Sensor resolution isn't the problem; bias stability is. A consumer gyro's drift is comparable to these signals, so the design depends on careful calibration, a rigid mount, turning the IMU during the flight, honest statistics, and **pooling many flights**.

How each choice was made, what was rejected, and how to check it: **[docs/METHODOLOGY.md](docs/METHODOLOGY.md)**. Before any flight result means anything, each IMU has to pass the bench validation in **[docs/BENCH.md](docs/BENCH.md)**.

## Hardware

Phone motion sensors vary too much between models, so the experiment is standardizing on one external IMU, the WitMotion WT901SDCL. It streams to the phone over Bluetooth. The phone supplies GNSS and runs the app. Two variants are supported:

- ICM-42605 gyro and accelerometer with an MMC3630 magnetometer, over Bluetooth 2.0 serial.
- MPU9250, over Bluetooth Low Energy 5.0.

WitMotion's product pages:

- <https://wit-motion.com/WirelessInclinometer/52.html>
- <https://wit-motion.com/WirelessInclinometer/50.html>

A rigid mount matters more than anything else for good results, because any slow turning of the sensor in its mount looks like signal. These are examples of mounts that hold firmly:

- [PivotCase PortaGrip phone mount](https://pivotcase.com/products/portagrip-phone-mount)
- [Arkon SkyHold windshield suction mount](https://arkon.com/products/skyhold-windshield-suction-phone-mount)

Pick a mount that lets you take the IMU out and put it back facing the opposite way, with the same side up. That turn, a few times per flight, is what makes a straight route count ([METHODOLOGY §9](docs/METHODOLOGY.md#9-turning-the-imu-in-flight-same-side-up)).

## Repository

| path | what |
|---|---|
| `android/` | The Android app (Kotlin/Compose). Connects to the IMU, logs its byte stream and GPS in the background, guides calibration, reminds you to turn the IMU, shows a live dashboard, and uploads or shares sessions |
| `server/` | Upload server (FastAPI + SQLite) that publishes every raw upload as an open dataset |
| `analysis/` | The `lll` Python package: decoding, single-session analysis and report, pooled analysis, a bench tool, and a synthetic-data generator |
| `docs/` | [METHODOLOGY](docs/METHODOLOGY.md) (decisions and how to check them), [MATH](docs/MATH.md) (equations), [EVIDENCE](docs/EVIDENCE.md) (reproducible simulation results), [BENCH](docs/BENCH.md) (hardware validation checklist), [FORMAT](docs/FORMAT.md) (file spec), [PROTOCOL](docs/PROTOCOL.md) (participant steps), shared test vectors |

## Quick start: analysis

```sh
python -m venv .venv && . .venv/bin/activate
pip install -e analysis -e server pytest httpx
lll synth demo.zip --truth sphere_rotating          # or sphere_still / flat_still; --variant spp|ble
lll synth hard.zip --truth flat_still --adverse     # temperature drift, turbulence, mount slip, climb/descent, GNSS gaps
lll analyze demo.zip                                # writes demo.result.json + demo.report.html
lll collate . -o collated --include-synthetic       # pools every *.result.json under . (synthetic data is excluded by default)
lll bench session.zip                               # bench statistics: decode, timing, quantization, Allan, reversal test
lll bench off.zip on.zip                            # compare two bench sessions (auto-zero off/on, two ranges)
pytest analysis/tests server/tests
python analysis/tests/evidence.py                   # regenerates docs/EVIDENCE.md
python analysis/tests/coverage.py                   # interval coverage under hardware faults (about 15 min)
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

Open `android/` in Android Studio, or run `./gradlew assembleDebug` (JDK 17 or 21, Android SDK 35). To set the default upload server for your build, use `lll.serverUrl` in `android/gradle.properties`. Users can change it in Settings. Choose and configure the IMU in Settings before the first session.

## Openness

- Code: **AGPL-3.0-or-later** © Scott Weisman.
- Data: **CC0** ([DATA_LICENSE.md](DATA_LICENSE.md)). Every upload is published as it arrived, including the IMU's full byte stream with the magnetometer.
- What's collected: [PRIVACY.md](PRIVACY.md).
- No analytics, ads or proprietary SDKs.

Reviews and criticism are welcome: [CONTRIBUTING.md](CONTRIBUTING.md).

---

Local Level Lab is an [Ars Astronomica](https://arsastronomica.com) project.
