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
