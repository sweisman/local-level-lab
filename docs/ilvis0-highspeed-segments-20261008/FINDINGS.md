# What the airborne measurements show

**The completed comparisons favor a rotating globe. None has a completed preference
for the specified flat disc.** This is the result of fitting NASA's archived aircraft
measurements, not a count of how many calculations finished for each model.

## Recordings and flight tracks

The measurements come from NASA's Operation IceBridge airborne lidar surveys over ice
sheets and related terrain. An **IMU (inertial measurement unit)** measures turning and
acceleration; GPS records the aircraft's track. Survey-grade Applanix systems supplied
the IMU increments used to reconstruct motion for precision mapping. NSIDC describes
ILVIS0 as an archive of [raw IMU and GPS data](https://nsidc.org/data/ilvis0/versions/1).

The analysis screened all **232 retained recordings**. It selected **53 complete, steady
stretches totaling 424.3 minutes**, each at least four minutes long with every supported
receiver ground-speed reading at least 700 km/h. Selection was saved before model fitting.
The [eligibility record](ELIGIBILITY.md) explains the motion, timing and completeness rules
and links to exact filenames, source fingerprints, UTC intervals, durations and speeds.
Several instruments recorded overlapping flight time; 53 stretches are not 53 independent flights.

The records contain Applanix **Group-4 angle and velocity increments**, with logged IMU
types 8 and 21 decoded separately. All 12 stretches with complete comparisons are IMU21;
the remaining 41 include 39 IMU21 stretches and two IMU8 stretches. A successful IMU8
decoder check is not a hardware identification or calibration certificate for IMU21.
The [detailed recording and track tables](FINAL_SUMMARY.md#source-recordings-and-tracks)
and [track positions](tracks.csv) preserve the source detail.

## Complete comparisons

Each stretch receives six fits: rotating globe, still globe and stationary flat disc,
under each of two processing cases. Both allow a constant gyro offset of ±1°/hour.
One assumes no Earth-rate removal; the other fits a shared removal fraction. These
checks allow for uncertainty in the logging system without changing the observations.

| Whole-stretch result | Stretches | Meaning |
|---|---:|---|
| Globe | 12 | All required fits finished; the better globe fit beats the flat disc in both processing cases. |
| Flat | 0 | No complete comparison favors the flat disc. |
| Unknown | 41 | At least one required fit did not pass the numerical stopping checks. |

**All 12 globe results also favor the rotating globe over the still globe in both
processing cases.** Shape is evaluated first; rotation is reported only after the
complete shape comparison favors globe.

The completed group totals 87.6 minutes, with a median stretch duration of 7.3 minutes
and median ground speed of 822.9 km/h. The unfinished group totals 336.6 minutes, with
medians of 8.9 minutes and 834.7 km/h. Faster or longer stretches did not consistently
make the numerical calculation easier in this already-fast selection.

## What the unfinished comparisons say

An unfinished comparison is not a finding that globe and flat fit equally well.
Of 318 individual fits, 188 passed the stopping checks and 130 did not. Most unfinished
fits exhausted their numerical allowance. Convergence means the parameter adjustment
finished; it does not mean the model fits the observations well.

Some unfinished stretches still supply a matched pair in which both calculations finished:

| Available comparison, across both processing cases | Globe fits better | Flat disc fits better |
|---|---:|---:|
| Rotating globe versus flat disc | 35 | 0 |
| Still globe versus flat disc | 30 | 26 |

The flat-favoring pairs are against the **still globe**. They do not establish that flat
beats the globe family, which also includes the rotating globe. Every available finished
rotating-globe/flat comparison favors the rotating globe. Where a required calculation
is missing, the full outcome remains unknown. These pairs reuse recordings and are not
independent votes. The [saved-result review](POST_RUN_REVIEW.md) gives the numerical details.

## Instrument quality and checks still outstanding

These are professional surveying instruments, not consumer phone IMUs. Their published
capabilities support investigating the degree-per-hour signals predicted here. The
[instrument guide](../ILVIS0.md#instrument-quality) distinguishes recorded instrument
types, published system performance and inferred hardware families.

The model observations are original IMU increments and receiver positions. The finished,
fused navigation solution is used for decoder validation and motion screening only.
"Raw" does not require the sensor to have had no internal calibration or filtering:
ordinary noise filtering can preserve slow turning. Automatic zeroing or subtracting
Earth rate is a different operation and can remove the signal. Exact legacy logging
corrections are still being investigated; fitting successfully does not identify them.

Many fits reach permitted calibration or mounting limits, and some are sensitive to
the integration clock. These are specific measurement-model checks, not evidence that
flat Earth fits as well. The study reports model fit preferences; it has not assigned
a validated probability of error or established that every fitted solution is the
best possible solution. The original measurements, failures and numerical evidence remain available.

## Pilot and next work

The earlier [six-recording pilot](../ilvis0-refinement-20261008/PROVISIONAL.md) reached
complete comparisons for two recordings. Both favored globe and then rotation under
all four tested cases. Two other recordings supplied globe-favoring partial pairs;
two had no finished shape pair. None had a resolved flat preference.

A [12-fit matched solver trial](../ilvis0-solver-trial-20261010/README.md) is running on
one completed control stretch and one unfinished stretch. It tests better numerical
stopping checks with the same measurements, models and physical assumptions. It does
not replace the preserved first-pass evidence or count incomplete fits as completed.

This page explains the results in plain language. The [original audited report](FINAL_SUMMARY.md)
and its numerical records remain unchanged for reproducibility.
