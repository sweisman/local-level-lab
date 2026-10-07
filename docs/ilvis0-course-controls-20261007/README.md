# What longer course measurements keep—and can hide

The bounded controls are complete. They support keeping the current acceptance gate while
investigating a more carefully defined motion check.

The same six files chosen for the IMU6 unit study contain five substantial recorded
ground-track changes: at least 3 degrees over 30 seconds, with complete receiver timing.
All five were detected at 2-, 6- and 12-second resolution in both receiver track and
navigation course. These are route changes, not independent measurements of aircraft yaw.
Only two of the six files supplied these controls, so this is limited evidence about
larger maneuvers rather than a complete flight-domain validation.

Short real corrections can disappear under averaging. Thirty-six deterministic controls
with known course changes tested durations from 0.2 to 40 seconds and rates from 0.06 to
0.5 degrees/second. The course-rate limit was held at 0.05 degrees/second.

| Course measurement interval | Controls that fall below the limit | Missed controls lasting at least 12 seconds |
|---|---:|---:|
| 2 seconds | 6 of 36 | 0 |
| 6 seconds | 12 of 36 | 0 |
| 12 seconds | 16 of 36 | 0 |

For example, a 0.1-degree correction over one second has a true rate of 0.1 degree/second.
The 12-second measurement reports a peak of only about 0.0125 degree/second and misses the
limit crossing. The 2-second measurement still detects this example. These controls are
deliberately noiseless course signals, not Earth-model simulations or an estimate of how
often actual aircraft make each maneuver.

This explains why the [53 resolution-sensitive files](../ilvis0-motion-61-20261007/README.md)
cannot automatically become accepted scientific windows. A longer timescale preserves the
tested substantial turns but can suppress real short corrections, just as it suppresses
measurement noise. It does not prove the original excursions were artifacts.

The implementation is `analysis/lll/ilvis0_motion_controls.py`. The worker completed after
the unit worker released its lock, keeping total numerical threads at two. Source hashes,
strict packet checks and GPS timing passed again in all six. Sources, inputs and numerical
environment are frozen separately in `data/ilvis0-course-controls-20261007/`; this directory
preserves the manifest, source snapshots and complete report. The scientific gate, stored
originals and frozen Earth-model studies remain unchanged.

A revised screening rule needs an explicit treatment of short aircraft motion and evidence
that the downstream analysis tolerates it. Selecting 12 seconds solely because it recovers
more data would not supply that evidence. No new motion interval has been adopted here.
