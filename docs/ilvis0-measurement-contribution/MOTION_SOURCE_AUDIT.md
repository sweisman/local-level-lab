# Can another instrument constrain aircraft motion?

The two stretches used in the gyro-free check have GPS positions and
accelerometer readings. A position track gives the direction of travel.
It leaves aircraft heading, pitch and bank undetermined. A measured
force direction also leaves the aircraft free to turn around that
direction. A second measurement would need to cover the same times and
constrain that freedom. [Gyro-free motion result](SHARED_GPS_MOTION_RATE_RESULT.md)

## What the catalogs show

| Selected stretch, UTC | Nearest timed LVIS images before and after | Other aircraft data |
| --- | --- | --- |
| IMU8, 2009-10-24 13:25:51–13:37:00 | 13:21:40.900 and 13:54:50.200 | No ILVIS0 `planedata` file listed for that date. |
| IMU21, 2011-10-12 12:05:40–12:13:02 | 11:46:00.900 and 12:47:02.700 | One NCAR RF04 netCDF file, listed as 19 MB, covers 11:31–21:40. ILVIS0 also lists `ILVIS0_planedata_55846_OIBGVrf04.asc` for that date. |

NASA's Common Metadata Repository returned zero timed image records
inside both stretches. The raw LVIS images are cataloged by day and
those entries alone cannot establish frame overlap. The Level-1A camera
times and reported orientations come from the accompanying navigation
system. A separate image-based attitude estimate would need overlapping
frames and a method that uses the image content. [IMU8 image query](https://cmr.earthdata.nasa.gov/search/granules.json?short_name=IOLVIS1A&temporal=2009-10-24T13%3A25%3A51Z%2C2009-10-24T13%3A37%3A00Z) ·
[IMU21 image query](https://cmr.earthdata.nasa.gov/search/granules.json?short_name=IOLVIS1A&temporal=2011-10-12T12%3A05%3A40Z%2C2011-10-12T12%3A13%3A02Z) ·
[LVIS image guide](https://nsidc.org/data/iolvis1a/versions/1)

NCAR's campaign example lists inertial-reference-system pitch, roll
and true heading. The distributed file reports one sample per second.
The example is from RF01, so RF04 field completeness, timing, processing
and agreement with the selected stretch still need verification.
The ILVIS0 file's relationship to NCAR RF04 is unknown. The catalog check
used metadata only. [NCAR data order and flight times](https://data.eol.ucar.edu/cgi-bin/codiac/fgr_form/id=351.003) ·
[Campaign example header](https://archive.eol.ucar.edu/raf/Projects/ICEBRIDGE/LRTdump.html) ·
[ILVIS0 aircraft file](https://cmr.earthdata.nasa.gov/search/granules.umm_json?concept_id=G3449174571-NSIDC_CPRD)

## What that would let us test

If RF04's source and timing checks pass, its angles could help describe
the size of pitch, roll and heading changes over complete seconds or
longer. A one-second report leaves motion inside that second unresolved.
Using that attitude in a fit would add a separate inertial reference and
its navigation assumptions. Any such check belongs alongside the gyro-free
comparison. The current model comparisons still have no measured aircraft
motion limit independent of inertial navigation.

## Which motion information could RF04 provide?

NCAR documents the Gulfstream V's aircraft attitude source as a
Honeywell inertial reference system. The campaign example marks the
pitch, roll and true-heading channels with an 80 ms time-lag magnitude.
It also lists an applied pitch calibration. The underlying channels
were sampled faster than 1 Hz, but the example supplies one output per
second. Confirm the timing correction and calibration on RF04 itself
before comparing onboard measurements.
[Campaign example header](https://archive.eol.ucar.edu/raf/Projects/ICEBRIDGE/LRTdump.html) ·
[NCAR processing guide](https://ncar.github.io/aircraft_ProcessingAlgorithms/3-the-state-of-the-aircraft)

Changes in attitude between successive samples could check
whole-second motion. Within-second motion can cancel between the two
samples. Even with exact attitudes, the net angle divided by the elapsed
time only gives a lower bound on the peak rate. The sampled
[acceleration-only rate check](RECORDED_MOTION_RATE_RESULT.md) would
need independent upper limits on motion at its own times to rule out
paths that rotate too fast.

The RF04 file is listed through NCAR's order form, which requests an
email address. The separate NASA aircraft file returned an authorization
error on direct download. The NASA metadata search returned no
`IANCR1B` granule for that date. NSIDC identifies NCAR as the archive
for `IANCR1B`, so that metadata gap does not contradict the RF04 listing.
The listed static pressure could also check relative height changes if
the file confirms a usable channel. Converting pressure changes to height
would still require atmospheric temperature and pressure information.
RF04 values and their exact instrument correspondence remain unverified.
[Tested RF04 intake and interpretation](NCAR_RF04_INTAKE.md) ·
[NSIDC dataset description](https://nsidc.org/data/iancr1b/versions/1) ·
[NCAR order form for RF04](https://data.eol.ucar.edu/cgi-bin/codiac/fgr_form/id=351.003) ·
[NASA aircraft-file catalog entry](https://cmr.earthdata.nasa.gov/search/granules.umm_json?concept_id=G3449174571-NSIDC_CPRD)
