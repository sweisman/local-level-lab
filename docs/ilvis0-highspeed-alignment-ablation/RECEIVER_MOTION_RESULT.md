# By GPS alone, 14 of the 16 recovered intervals fall inside the published range

The 16 intervals [recovered without the navigation-status flag](RESULT.md)
were profiled using GPS positions only, alongside the 53 published
stretches. All 69 profiles completed. Fourteen recovered intervals are
inside the range of the published stretches on every measure. Two are just
outside on one measure each. [Fixed plan](RECEIVER_MOTION_PLAN.md) ·
[Per-interval table](receiver-motion.csv)

No gyro, accelerometer or navigation-computer value was used, and no Earth
model was evaluated.

| Measure | Published 53, smallest to largest | Recovered 16, smallest to largest |
| --- | ---: | ---: |
| Climb rate, 95th percentile | 0.13 to 0.40 m/s | 0.15 to 0.29 m/s |
| Climb rate, largest | 0.15 to 0.52 m/s | 0.17 to 0.33 m/s |
| Course change, 95th percentile | 0.0012 to 0.0135°/s | 0.0013 to 0.0151°/s |
| Course change, largest | 0.0014 to 0.0189°/s | 0.0016 to 0.0169°/s |
| Lowest ground speed | 712.7 to 908.6 km/hour | 712.7 to 908.1 km/hour |

Every value in both groups is well under the reference values of the
earlier profile, 1.5 m/s of climb and 0.05°/s of course change.

## The two intervals outside the range

- **12 October 2015.** Its 95th-percentile course change is 0.0151°/s,
  against 0.0135°/s for the largest published stretch. Its largest single
  value is inside the range. Over 6.3 minutes its direction of travel
  changed by 1.3°. This is one of the two recovered intervals on flight
  time with no published stretch.
- **22 October 2015.** Its lowest ground speed is 0.002 km/hour below the
  lowest published value. That published value is the main recorder's
  stretch on the same leg of the same flight.

The other recovered interval that adds flight time, 17 October 2011, is
inside the range on every measure.

## What this does and does not show

Seen through GPS, the recovered intervals were flown about as straight and
level as the published ones. On this evidence the navigation-status flag
did not keep out rougher flying. It kept out one recorder.

GPS shows the path of the antenna. It does not show the aircraft's roll or
where its nose points. None of the 16 intervals has been accepted for
fitting. That still needs a check of the information each carries about
every fitted parameter, and a fixed fitting plan. The published 53-stretch
study is unchanged.

All 69 tasks completed with zero Earth-model fits. Three focused software
tests passed. [Saved metrics and receipt](receiver-motion-result.json)

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.ilvis0_review_checks_report receiver-motion
```
