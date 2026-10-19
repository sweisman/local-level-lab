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

For new work use at most **four numerical threads in total**, shared across active jobs.
One worker can use four threads, two workers can use two each, or four workers can
use one each. Frozen studies retain their recorded settings, including earlier
two-thread freezes. Reserve other active jobs' allocations before launching;
completed recovery studies must not be restarted.

The guard rejects oversubscription and sets numerical-library limits before imports:

```sh
~/venv/bin/python analysis/tests/run_numerical.py -- ~/venv/bin/python -m pytest analysis/tests
```

Use `--workers 2` for a target running two concurrent workers. While another job
uses two threads, include `--reserved-threads 2`. The guard validates the declared
allocation; it does not discover other jobs or set the target's worker count.
New launchers may instead call `lll.compute_budget.environment` before numerical
imports and freeze the validated allocation. Historical launch commands and limits
remain part of their original freezes. Expensive
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
recording. New participant sessions are stationary A/B recordings; aircraft identity,
placement and flight dashboards are removed from the active flow. Session schema 3 adds
a versioned stationary metadata object while retaining historical flight archives.
The legacy airline asset and its ODbL license remain for historical reproducibility.

Use `lll analyze stationary.zip` for the new preliminary signed-rate report. It skips
airborne fitting and estimates no latitude curve or calibrated significance. The existing
flight collator is not a stationary population estimator; do not apply its thresholds
or unit certificates to ground recordings. See [the stationary method](STATIONARY.md).

## Documentation and reproducibility

The [public website build](../website/README.md) renders the root README and linked
Markdown as a GitHub Pages site at locallevellab.com. Data downloads and source files
remain on GitHub. Website dependencies and checks are separate from the frozen
numerical environment; building the site runs no scientific analysis.

Public guides explain the method and current evidence without requiring raw research files.
[MATH](MATH.md), the [technical methodology record](METHODOLOGY_TECHNICAL.md),
[technical validation record](VALIDATION_TECHNICAL.md), [technical bench checklist](BENCH_TECHNICAL.md)
and [recording format](FORMAT.md) preserve equations, thresholds, commands and data contracts.
[Contributing](../CONTRIBUTING.md) describes checks appropriate to a proposed change.

## Historical aircraft route replay and design

The [core-pipeline handoff](core-pipeline-20261006/README.md) documents the new optional research
paths and frozen prospective inputs. Preparation writes specifications and cost bounds without
running flights. Geometry search uses assumed axes and a finite uncertainty grid; empirical
policies remain unavailable for observed-track replay. A campaign or nontrivial optimizer search
requires a separate compute budget. Future work shares a four-thread total budget;
historical freezes keep their original worker and numerical-thread settings.
