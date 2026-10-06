<p align="center"><img src="docs/img/logo.png" alt="Local Level Lab logo" width="200"></p>

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
| `docs/PRIMARY_CORPUS.md` | Curator approval, bench certificates, provisional primary gates and migration |
| `analysis/` | The `lll` Python package: decoding, single-session and pooled analysis, bench tools, synthetic data, turn optimization, and independent research calibration/validation |
| `docs/` | [METHODOLOGY](docs/METHODOLOGY.md) (decisions and how to check them), [MATH](docs/MATH.md) (equations), [EVIDENCE](docs/EVIDENCE.md) (reproducible simulation results), [VALIDATION](docs/VALIDATION.md) (analysis candidates, campaign plans and current limitations), [BENCH](docs/BENCH.md) (hardware validation checklist), [FORMAT](docs/FORMAT.md) (file spec), [PROTOCOL](docs/PROTOCOL.md) (participant steps), shared test vectors |

## Quick start: analysis

Requires Python **3.11 or newer**. The lockfile records the Python 3.14 validation environment;
on older supported interpreters install the packages' compatible dependencies instead of that lockfile.

```sh
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-lock.txt -e analysis -e server   # exact versions; every result records them
lll synth demo.zip --truth sphere_rotating          # or sphere_still / flat_still; --variant spp|ble
lll synth hard.zip --truth flat_still --adverse     # temperature drift, turbulence, mount slip, climb/descent, GNSS gaps
lll analyze demo.zip                                # writes demo.result.json + demo.report.html
lll collate . -o collated --include-synthetic       # pools every *.result.json under . (synthetic data is excluded by default)
lll bench session.zip                               # bench statistics: decode, timing, quantization, Allan, reversal test
lll bench a.zip b.zip                               # compare two bench sessions (two ranges, two units)
pytest analysis/tests server/tests
python analysis/tests/evidence.py                   # regenerates docs/EVIDENCE.md
python analysis/tests/coverage.py                   # interval coverage under hardware faults (about 15 min)
```

## Analysis validation status

Software 0.6.0 uses eligibility policy **pilot-2** by default. Opt-in research candidates use
the shared **candidate-eligibility-2** policy across analysis, research and calibration.
The candidate engine includes weighted SVD and identifiable-subspace model tests, dynamic
sensor bias, dynamic or wind-driven crab, forward-axis uncertainty, and complete nonlinear
bootstrap refits. Its primary identifiability gate evaluates trajectory geometry at all three
model anchors; the free-fit SVD remains a diagnostic. The turn optimizer prioritizes estimable
contrasts and their retention margin across the selected nuisance models.

The initial [development pilots](docs/bootstrap-development-20261005.json) completed 18 flights
across all three truths, mixed-bias and wind scenarios. Every run passed candidate eligibility
and bootstrap convergence, with test rank 2. A separate earlier run had rank 1; operational
calibration therefore keeps ranks separate and abstains at uncalibrated ranks. These small
pilots establish feasibility for one experimental [75-minute geometry](docs/development-protocol-75min.json),
not false-rejection control or a validated flight domain.

The required order is development geometry/stability screening, a frozen source/configuration/
numerical environment, fresh threshold calibration, then independent validation. Calibration
and validation have separate exact sample-size criteria. The [proposed flight campaign](docs/flight-calibration-proposed-manifest-20261005.json)
has not run; **no fresh empirical threshold or 3σ validation claim is available**. Pairwise
decisions and pooling are experimental and require their own calibration rules. Commands,
deterministic geometry stress cells, campaign costs and promotion requirements are in
[VALIDATION.md](docs/VALIDATION.md).

The bounded [**1,000-flight development campaign**](docs/development-1000-20261005/campaign.json.gz)
completed in **3 hours 16 minutes**: 906 flights passed eligibility, with zero analysis failures
and valid bootstrap convergence in every fit. One eligible flight rejected its generating model
under the diagnostic rule. Observed ranks were 927 rank-2 and 73 rank-1; moving the rank cutoff
by ±10% changed rank in 47 flights. Wind cases had lower acceptance than mixed-bias cases.
These findings require fresh calibration and rank/geometry review before independent validation.
Detailed results and remaining work are in [VALIDATION.md](docs/VALIDATION.md#completed-development-results-2026-10-06)
and the [campaign handoff](AGENTS.md#analysis-campaign-handoff--2026-10-05).
A [saved-record selection review](docs/VALIDATION.md#selection-review-from-saved-records-2026-10-06)
quantifies proposed rank-margin gates. The subsequent
[eight-case magnetic diagnostic](docs/VALIDATION.md#magnetic-watchdog-diagnostic-and-next-pilot-2026-10-06)
confirmed that wind can trigger conservative segment exclusions without mount creep.
Analysis now labels that ambiguity explicitly and retains the protective exclusions.
The [second **1,000-attempt development pilot**](docs/development-1000-20261006/README.md)
completed in **3h24m**, with zero analysis failures, 905 eligible flights (884 rank 2), and
zero eligible diagnostic rejections of the generating model. Bootstrap was valid in 998 fits;
the two invalid rank-0 fits were excluded. The preregistered rank margin excluded all 53 flights
that changed rank under a ±10% cutoff sweep. Results and lossless checkpoints are saved.
This pilot precedes fresh calibration. The refreshed
[calibration proposal](docs/research-next-stage-20261006/calibration-proposed-manifest.json) remains unrun
and must be reviewed against the prepared geometry cases before approval; full calibration and validation
still cost approximately 486,000 attempts / 69 serial days at the new pilot's measured
rank-2 acceptance and runtime, before an attempt reserve. This is a point estimate, not an
approved budget or a validated false-rejection claim.

[Next-stage preparation](docs/research-next-stage-20261006/README.md) compares both pilots
under the common 10% gate, preserving the first pilot's diagnostic rejection. It prepares
24 synthetic geometry cases and five observed-track windows, while retaining two coverage-blocked
tracks. A prospective turn-spacing bug is fixed and the restricted calibration proposal is
refrozen. The conditional attempt reserve is about 561,000 attempts / 80 serial days. No
additional simulations, calibration or validation have run; real IMU testing awaits hardware.

Three [observed flight tracks](docs/flight-geometry-20261006/README.md) are also normalized for
future development geometry tests. They provide real position/course histories at coarse sampling;
simulated sensor and nuisance processes will remain explicit. They supply no IMU validation evidence.
Four further [directly scraped public tracks](docs/scraped-flight-geometry-20261006/README.md)
cover high latitude, the equator, and Europe/Middle East–South Africa routes. Source estimates
and coverage gaps are preserved and excluded from reported-position coverage calculations.

## Server

```sh
lll-server --data /srv/lll serve --host 127.0.0.1 --port 8000   # put Caddy/nginx in front for TLS
lll-server --data /srv/lll process        # analyze new uploads → reports
lll-server --data /srv/lll process --reprocess # explicitly regenerate stored results after an analysis upgrade
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

## Flight identity and GPS recovery

Flight setup requires a searchable airline selection, its operating flight number, the departure
date at the origin, and airport codes. The offline directory contains 6,136 coded OpenFlights
records, including historical carriers; listing is not verification that a flight operated.
Use **Open flight history** to check the date and route. If phone GPS is missing, keep recording
the IMU and save a public track after landing. It can cross-check GPS and potentially recover
geometry, subject to observed coverage, time alignment and uncertainty checks. Automatic
external-track fallback is not yet part of the scientific analysis. See [the protocol](docs/PROTOCOL.md).

The protocol covers codeshares, delayed flights crossing midnight, missing-GPS recording and
what to preserve in a downloaded track. [Privacy](PRIVACY.md) explains the external browser lookup;
[validation](docs/VALIDATION.md#external-flight-tracks-and-missing-gnss) records the remaining
scientific work before an external track can replace phone GNSS.

The bundled airline directory is [OpenFlights data](https://openflights.org/data.php), licensed
under ODbL-1.0; its license is in `android/app/src/main/assets/airlines-LICENSE.txt`.

## Openness

- Code: **AGPL-3.0-or-later** © Scott Weisman.
- Data: **CC0** ([DATA_LICENSE.md](DATA_LICENSE.md)). Every upload is published as it arrived, including the IMU's full byte stream with the magnetometer.
- What's collected: [PRIVACY.md](PRIVACY.md).
- No analytics, ads or proprietary SDKs.

Reviews and criticism are welcome: [CONTRIBUTING.md](CONTRIBUTING.md).

---

Local Level Lab is an [Ars Astronomica](https://arsastronomica.com) project.
