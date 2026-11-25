# The aircraft's own flight records for 2011 and 2015

The NASA recordings used in this project come from a laser instrument that
carried its own **IMU (inertial measurement unit)**, the device whose
gyroscopes and accelerometers supply the measurements, and its own GPS
receiver. In 2011 and 2015 the instrument flew on a research jet operated by
the National Center for Atmospheric Research (NCAR). NCAR publishes a
separate one-second record of every research flight from the aircraft's own
navigation system and a different GPS receiver. These records give a second
view of how the aircraft moved on the selected stretches.

## What was received

Seventeen flight files were taken in unchanged, three from the
[2011 campaign](https://doi.org/10.5065/D6R49P35) and fourteen from the
[2015 campaign](https://doi.org/10.5065/D6H70D6N). Each file identifies the
campaign, the aircraft (N677F), the flight number and the date, and each has
a UTC clock with one report every second and no gaps.

| Campaign | Flights received | Selected stretches inside them |
| --- | --- | ---: |
| 2011 | 8, 10 and 12 October | 3 |
| 2015 | 24 September to 22 October, fourteen flights | 29 |

All 32 stretches have roll, pitch, heading and GPS position for every
second. Three of the 2015 flights (1, 14 and 19 October) contain no selected
stretch.

Nine selected stretches, three each on 25, 27 and 29 October 2015, have no
aircraft record. The 2015 set lists no research flight after 22 October.
Twelve more stretches come from other campaigns, which these two sets of
records do not cover.

## How the records are used

The records are compared with the instrument's own GPS track and with the
rotation its gyroscopes recorded. They are not used to choose stretches, and
they do not enter any globe or disc fit.

- [Comparison result](MOTION_MATCH_RESULT.md): the two GPS tracks agree to
  about a metre across the direction of flight on all 32 stretches.
- [Turning at the measured time difference](MOTION_LAG_RESULT.md): once
  the gyro windows are moved by the 0.4 s found in the GPS tracks, the
  one-second turning agrees to a median of 0.014°.
- [Comparison plan](MOTION_MATCH_PLAN.md)
- [Intake summary](intake.json): file fingerprints, clock checks and the
  seconds found for each stretch.

The flight files stay in local storage. Each is a few megabytes and can be
requested again from the two links above.

```sh
~/venv/bin/python -I analysis/lll/ncar_aircraft_records.py \
  --downloads /path/to/files \
  --stretches docs/ilvis0-highspeed-segments-20261008/eligible-stretches.csv \
  --destination data/ncar-aircraft-records \
  --output docs/ncar-aircraft-records/intake.json
```
