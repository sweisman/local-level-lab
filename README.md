<p align="center"><img src="docs/img/logo.png" alt="Local Level Lab logo" width="160"></p>

# Local Level Lab

**Testing Earth’s curvature with airborne lidar survey measurements.**

An aircraft flying level over a globe gradually turns as the direction of local down
changes along its route. At 900 km/h, following that curve means about eight degrees
of turning per hour. That is a measurable prediction.

An **IMU (inertial measurement unit)** contains gyroscopes and accelerometers.
**The central measurement is the gyroscope record: how the aircraft actually turns.**
Accelerometers help reconstruct its motion; GPS supplies route, speed and timing.
Local Level Lab tests those recorded movements against globe and flat-disc predictions.
The measurements, code and results are open.

## What the measurements show

<!-- current-status:start -->
**53 globe preferences, 0 flat preferences, 0 unresolved** among 53 preselected stretches.
See the [verified current status](docs/CURRENT_STATUS.md) for coverage, background-field comparisons and the supporting result records. All selected comparisons have passed their required numerical checks.
<!-- current-status:end -->

**All 53 stretches now pass their required numerical comparisons and favor the
globe under both tested processing cases.** The original run completed twelve;
the remaining 41 have now passed separately checked recoveries using the same
measurements and selected intervals.

![Recorded gyro motion across all 53 flight stretches, with a median line](docs/ilvis0-gyro-overview/raw-pitch.png)

**The recorded motion has a consistent direction: all 53 traces finish nose-down.**
Each thin line sums the raw gyro increments around the aircraft's pitch axis,
starting at zero; the thick line shows the median. No fitted corrections or GPS
values enter these angles. The graph includes every selected stretch.

This is a direct visualization of the measurements, not a separate curvature test:
aircraft motion and the background rotation field also contribute. The full analysis
accounts for those contributions when comparing shapes.
[How to read the graph and download its data](docs/ilvis0-gyro-overview/README.md).

On the original twelve completed comparisons, median horizontal fitting error was
about **7 centimetres for the globe with a background rotation field, versus
47 metres for the flat disc**. These describe agreement with the positions used in
fitting; prediction on unused observations is a separate check.

A [measurement-contribution check](docs/ilvis0-measurement-contribution/README.md)
on eighteen stretches preserves the globe preference in all 36 processing-case
comparisons when height is removed from the score. Those scores reuse the
existing fitted parameters; horizontal-only refitting is being qualified separately.

**[See all 53 stretches](docs/ilvis0-current-findings-20261015/STRETCHES.md)** —
instrument configuration, duration, speed, course, latitude and current result.
**[Download the comprehensive CSV](docs/ilvis0-current-findings-20261015/stretch-analytics.csv)**
for measured rate summaries, velocities, model predictions, fit costs, stopping
reasons and shared-track identifiers; [column definitions](docs/ilvis0-current-findings-20261015/ANALYTICS.md)
explain which quantities are measurements and which are diagnostics.

## Where the data come from

NASA’s Operation IceBridge aircraft carried survey-grade Applanix IMUs and GPS
receivers for lidar mapping of ice sheets, glaciers and sea ice. Measuring the
surface accurately requires knowing where the aircraft was and how it was oriented.
These recordings are source material for that work.

The analysis works from the recorded IMU increments, rather than treating the
instrument’s finished navigation answer as evidence.

## Gyroscope measurements, GPS context

GPS locates the flight so each model can predict the turning associated with its
route. Receiver positions also constrain the reconstructed track during fitting.
**GPS is the positioning system; WGS84 is the coordinate reference used for its
reported positions.** Those conventions remain part of the analysis. Planned
[measurement-contribution checks](docs/NEXT_STEPS.md#then-strengthen-the-interpretation)
will isolate how much separation comes from the gyro measurements and how much
depends on other inputs.

Select steady, complete stretches of at least four minutes and 700 km/h throughout,
**before examining model preferences**. Fit each whole stretch with the same permitted
instrument errors under globe-with-field, zero-field globe and stationary flat-disc
candidates. Compare shape first, then the background field.

The completed comparisons are substantial evidence favoring the globe in this test.
A statistical significance level has not yet been calibrated, and overlapping
recordings cannot be counted as independent flights.

Earth’s shape, a measured rotation field and the cause of that field are separate
questions. A globe result does not decide geocentrism versus heliocentrism. The
current background-field comparison neither identifies its cause nor measures a
solar-versus-sidereal rate difference.

## Follow the work

- **[Studies and what each added](docs/STUDIES.md)** — a concise guide to the analyses,
  successful recoveries and approaches that did not qualify.
- **[How the method works](docs/METHODOLOGY.md)** — observations, models and checks.
- **[What comes next](docs/NEXT_STEPS.md)** — measurement-contribution checks,
  stronger prediction tests and a freely measured rotation rate.
- **[Archive and instrument guide](docs/ILVIS0.md)** — source data, decoding and provenance.

## A separate ground experiment

A crowdsourced experiment is under development: place a smaller IMU on a solid,
level surface, record, reverse it by 180° and repeat. The aim is to measure a signed
horizontal rotation signal at different latitudes without giving the analyzer an
expected rate. Consumer-device sensitivity still needs testing.
See the [ground experiment](docs/STATIONARY.md) and [participant instructions](docs/PROTOCOL.md).

[Developer setup](docs/DEVELOPMENT.md) · [Contributing](CONTRIBUTING.md) ·
[Privacy](PRIVACY.md) · [Data licensing](DATA_LICENSE.md).
Code: AGPL-3.0-or-later. An [Ars Astronomica](https://arsastronomica.com) project.
