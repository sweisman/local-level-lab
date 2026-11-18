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
**53 with the specified-field globe preferred, 0 flat-disc preferences, 0 without a consistent preference** among 53 selected stretches.
See the [verified current status](docs/CURRENT_STATUS.md) for coverage, background-field comparisons and the numerical checks recorded for each cohort.
<!-- current-status:end -->

The original run completed 12 comparisons. Later numerical studies completed
the other 41 using the same stretches and a series of different numerical checks.
The stretches span 27 recording dates. Forty-nine are concentrated between
about 57°S and 64°S, and some share a flight or instrument.

![Recorded gyro motion across all 53 flight stretches, with a median line](docs/ilvis0-gyro-overview/raw-pitch.png)

**The recorded motion has a consistent direction: all 53 traces finish nose-down.**
Each thin line sums the raw gyro increments around the aircraft's pitch axis,
starting at zero; the thick line shows the median. No fitted corrections or GPS
values enter these angles. The graph includes every selected stretch.

This is a direct visualization of the measurements, not a separate curvature test:
aircraft motion and the background rotation field also contribute. The full analysis
accounts for those contributions when comparing shapes.
[How to read the graph and download its data](docs/ilvis0-gyro-overview/README.md).

![The same 53 gyro traces with the specified background-field prediction subtracted](docs/ilvis0-background-subtracted/background-subtracted.png)

**Subtracting the specified background field leaves all 53 traces ending
nose-down.** This uses the same gyro bins, but the correction uses GPS latitude
and direction with an assumed level attitude. Aircraft motion remains; the
background rate is supplied rather than measured by this plot.
[What was subtracted, and the plotted data](docs/ilvis0-background-subtracted/README.md).

![Gyro tilt after subtracting the specified background field and estimated aircraft maneuvers](docs/ilvis0-motion-subtracted/motion-subtracted.png)

**All 52 traces with a complete maneuver estimate still finish nose-down after
that estimate is removed.** This illustration uses the instrument’s fused
navigation attitude. That solution already uses the gyros and a globe navigation
model, so the correction shares those assumptions.
[Correction and omitted stretch](docs/ilvis0-motion-subtracted/README.md).

A [route-based companion](docs/ilvis0-gyro-companion-v2/INTERPRETATION.md) compares
these raw rates with geographic predictions, without fitting gyro corrections.
Median rate differences are **0.88°/h for globe plus the specified field,
2.84°/h for zero-field globe, and 5.87°/h for the level flat prediction**.
Aircraft motion remains in this descriptive comparison.

A [three-recording prediction pilot](docs/ilvis0-retrospective-prediction-pilot-v2/INTERPRETATION.md)
calibrated on earlier measurements and checked later GPS positions without
using them to adjust the answer. One recording completed all required settings:
horizontal RMS was **0.84–1.13 m for globe plus the specified field, about 496 m
for zero-field globe and 793 m for disc**. The other two recordings have missing
fits or failed accuracy checks. These are development results; statistical
confidence and independent confirmation remain open.

Separate [height-removal checks](docs/ilvis0-measurement-contribution/README.md)
preserve the horizontal score advantage, but allow unrealistic vertical paths.
One of two refitted stretches passed every repeat check; the other remains
unresolved after a matched timing search. These test what drives the result;
they do not replace the complete 53-stretch analysis.

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

## How the comparison works

1. **Apply the published selection rules.** Each chosen stretch
   has complete, usable measurements for at least four minutes and a GPS ground
   speed of at least 700 km/h throughout. The selected set was fixed for its own
   fits after earlier exploratory archive fitting.
2. **Make the same comparison on each stretch.** The software reconstructs the
   flight from IMU measurements under a globe with a specified background
   angular field, a globe with no such field, and a stationary flat disc. It
   gives each candidate the same permitted instrument corrections.
3. **Declare the instrument assumptions.** Each fitted gyro axis can have
   a constant offset of up to ±1°/hour. This is an assumed limit. The analysis
   also tests two assumptions about possible onboard subtraction of the field.
4. **Compare the fitted models.** The shape rule compares the stationary
   disc with the better of the two globe fits. If globe wins, the two globe
   fits are compared for the field result.

The **specified field** is an angular-rate pattern supplied to the calculation;
this test does not estimate its rate freely. The GPS receiver reports latitude,
longitude and height using WGS84, a standard geographic coordinate reference.
The comparison therefore has stated coordinate assumptions. The [method page](docs/METHODOLOGY.md)
explains how the recorded IMU and receiver streams are kept separate.

The globe with the specified field fits best in all 53 stretches under both
processing assumptions. Comparing only the zero-field models, the disc fits
better than the globe in 18 stretches under both assumptions. The next controls
will test how much of the separation comes from curvature, the supplied field
and the gyro offset limit. Statistical confidence for aircraft remains open.

## Follow the work

A [withheld ESA forecast check](docs/prediction-observed-development/ROLLING_ORIGIN_400_CONDITIONAL_RESULT.md)
had a raw horizontal RMS error of 5.38 m on one development recording.
After conditioning on earlier receiver errors, the horizontal RMS error was 0.56 m
and the height RMS error was 0.17 m.

A [matched three-model ESA development check](docs/prediction-observed-development/ESA_400_120_MODEL_MATRIX_INTERPRETATION.md)
now supplies two complete withheld-position settings, both favoring globe;
two other settings remain unresolved after flat-model stopping failures.
Aircraft uncertainty and independent confirmation are still open.

The [prediction pilot](docs/ilvis0-retrospective-prediction-pilot-v2/INTERPRETATION.md)
now succeeds on one complete recording-level comparison. A separate
[ESA development comparison](docs/esa-observed-wide-pilot/INTERPRETATION.md) now
completes three matched settings: typical later 3D position error is **about
15 m for globe plus the specified field, 3.8–4.4 km for zero-field globe and
7.4–8.6 km for disc**. These reuse one twenty-minute recording; the fourth
setting is incomplete because two starts reached the runtime ceiling.
The [corrected solver](docs/timing-matrix-combined/README.md) now passes all
48 development cases and 24 comparisons between prescribed starting points,
under the original limits. Earlier failed runs remain recorded. A
[complete calibration](docs/prediction-calibration-host-20261030/INTERPRETATION.md)
now passes all 7,176 fits across 299 simulated cases and supplies a verified
prediction-error limit. A [separate continuation of the independent test](docs/HOST_PREDICTION_STATUS.md)
completed all 4,344 fits across 181 fresh simulated cases and passed its declared
coverage rule. That test validates the procedure under simulated conditions;
aircraft error coverage remains unestablished.
Statistical confidence is tested separately; independent ESA confirmation
follows method qualification. Shared recordings are grouped
before validation; ESA recording 187 is development material and the other
cataloged groups are reserved for confirmation. A freely measured rotation
field and solar-versus-sidereal precision come later.

- **[Studies and what each added](docs/STUDIES.md)** — a concise guide to the analyses,
  successful recoveries and approaches that did not qualify.
- **[How the method works](docs/METHODOLOGY.md)** — observations, models and checks.
- **[Reproduce the studies](docs/REPRODUCIBILITY.md)** — shared code and verified historical evidence.
- **[What comes next](docs/NEXT_STEPS.md)** — measurement contributions,
  withheld predictions, protected ESA confirmation and later rotation-field work.
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
