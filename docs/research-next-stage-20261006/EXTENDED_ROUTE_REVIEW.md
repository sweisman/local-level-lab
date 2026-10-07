# Longer recordings on the observed routes

Longer recordings can provide more usable cruise, but the tested windows still do not
separate the physical models from allowed IMU drift and aircraft uncertainty.

The new check samples three- and four-hour windows every 15 minutes across the seven saved
tracks. It tries no IMU turns, three or six distributed turns, and three centrally placed
six-turn patterns spaced 20 minutes apart. The central patterns differ by five minutes.
Every pattern respects the existing six-turn limit, spacing rule and aircraft-maneuver buffer.
The flight path itself is unchanged.

| Window length | Windows checked | Passed position-coverage check | Window/turn combinations passing preliminary geometry | Passed any nominal model contrast |
|---|---:|---:|---:|---:|
| Three hours | 150 | 21 | 10 | 0 |
| Four hours | 127 | 6 | 0 | 0 |

The short Singapore–Bali track cannot supply either window length; Chicago–Los Angeles
cannot supply four hours. Most other windows fail because less than 95% of their duration
has supported, reported positions. Gaps and provider estimates remain unsupported.

The ten preliminary passes are six Abu Dhabi–Chicago combinations and four Chicago–Los
Angeles combinations. All are westbound. The recorded eastbound Chicago–Abu Dhabi windows
that pass coverage still fail the required heading diversity. No heading rule was relaxed.

The ten passing combinations were checked at all three physical-model anchors, under both
wind descriptions, with dynamic IMU bias and forward-angle uncertainty retained. At the
nominal zero-wind/zero-angle settings, none retains enough of any model contrast after
accounting for the nuisance parameters. More time did not resolve that ambiguity here.

This took 2.65 seconds and generated no simulated flights. It is a limited search of
overlapping windows and fixed schedules, not proof that every schedule fails. Interpolated
motion between the coarse position fixes is an assumption. Full sensor preprocessing,
orientation recovery, nuisance-envelope evaluation and decision calibration were not run.

The earlier two-hour screen checked another 176 windows and found seven preliminary passes,
also with no nominal model-contrast pass. Together these checks cover 453 overlapping windows
and 17 preliminary passing combinations. They provide no validated protocol or Earth-model
conclusion. Next work should vary safe turn timing or obtain better actual-route coverage;
simply increasing the recording length has not been sufficient in these controls.

For reproducibility, `analysis/tests/screen_extended_route_controls.py` writes the full
window outcomes, timing definitions, source hashes and limitations to
`extended-route-controls.json`. A preserved `extended-route-controls-first-pass.json`
contains an invalid preliminary run: three attempted timing patterns exceeded six turns,
so 27 covered windows were blocked by schedule validation. It is not a geometry result.
The corrected helper validates pattern definitions before reading the tracks.
