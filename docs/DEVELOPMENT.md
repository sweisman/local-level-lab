# Developer setup and tools

This is the technical setup guide. For the experiment itself, start with the [README](../README.md)
and [methodology](METHODOLOGY.md). Collecting a recording and validating a scientific result
are separate tasks; see [Validation](VALIDATION.md).

## Analysis

Python 3.11 or newer is supported. The lockfile records the Python 3.14 validation environment;
older supported interpreters need compatible dependency versions instead. These examples use
an existing virtual environment at `~/venv`; do not install into system Python.

```sh
~/venv/bin/python -m pip install -r requirements-lock.txt -e analysis -e server
~/venv/bin/lll synth demo.zip --truth sphere_rotating
~/venv/bin/lll analyze demo.zip
~/venv/bin/lll collate . -o collated --include-synthetic
~/venv/bin/lll bench session.zip
~/venv/bin/python -m pytest analysis/tests server/tests
```

Synthetic sessions are excluded from ordinary collation; the example explicitly enables them.
Analysis produces a machine-readable result and an HTML report. Neither a software quality label
nor a provisional significance value establishes validated scientific eligibility.

For routine work use at most two CPU threads/workers total. A single numerical process can use
`OPENBLAS_NUM_THREADS=2`, `OMP_NUM_THREADS=2` and `MKL_NUM_THREADS=2`; parallel workers must share
that total budget. Frozen campaigns must retain their recorded thread settings. Expensive
simulation campaigns have their own explicit case and time budgets; a resource setting is not
permission to launch them. The historical evidence generator runs simulations and prints
Markdown for the technical evidence record; it is not a lightweight documentation check.

## Upload server

```sh
~/venv/bin/lll-server --data /srv/lll serve --host 127.0.0.1 --port 8000
~/venv/bin/lll-server --data /srv/lll process
~/venv/bin/lll-server --data /srv/lll process --reprocess
~/venv/bin/lll-server --data /srv/lll collate
~/venv/bin/lll-server --data /srv/lll export dump/
```

Use a reverse proxy for TLS, upload limits and public deployment. Raw archives remain unchanged
when generated reports are reprocessed. The [curation guide](CURATION.md) describes instrument
registration, bench certification, session approval, migration and deployment constraints.

Public endpoints are upload and index at `/api/v1/sessions`, session metadata at
`/api/v1/sessions/{id}`, original archives at `/api/v1/sessions/{id}/raw`, session reports at
`/api/v1/sessions/{id}/report`, and the pooled report at `/report`.

Configuration uses `LLL_DATA`, `LLL_MAX_UPLOAD_MB` (default 200), `LLL_MAX_UNCOMPRESSED_MB`
(default 2000), and `LLL_UPLOADS_PER_HOUR` (default 20). Per-IP limits use the address seen
by the application, so configure trusted forwarding correctly behind a proxy.

## Android

Open `android/` in Android Studio. The build uses Android SDK 35 and JDK 17 or 21. In this
workspace use the installed JDK under `~/.local/jdk21` and limit Gradle to two workers:

```sh
env JAVA_HOME="$HOME/.local/jdk21" ./android/gradlew --project-dir android --max-workers=2 assembleDebug
```

The default upload destination can be set with `lll.serverUrl` in `android/gradle.properties`.
Users can change it in Settings. Choose the Bluetooth variant and verify IMU settings before
recording. The bundled airline directory is OpenFlights data under ODbL-1.0; its separate
license accompanies the asset.

## Documentation and reproducibility

Public guides explain the method and current evidence without requiring raw research files.
[MATH](MATH.md), the [technical methodology record](METHODOLOGY_TECHNICAL.md),
[technical validation record](VALIDATION_TECHNICAL.md), [technical bench checklist](BENCH_TECHNICAL.md)
and [recording format](FORMAT.md) preserve equations, thresholds, commands and data contracts.
[Contributing](../CONTRIBUTING.md) describes checks appropriate to a proposed change.

## Experimental route replay and design

The [core-pipeline handoff](core-pipeline-20261006/README.md) documents the new optional research
paths and frozen prospective inputs. Preparation writes specifications and cost bounds without
running flights. Geometry search uses assumed axes and a finite uncertainty grid; empirical
policies remain unavailable for observed-track replay. A campaign or nontrivial optimizer search
requires a separate compute budget. Keep at most two total numerical threads/workers.
