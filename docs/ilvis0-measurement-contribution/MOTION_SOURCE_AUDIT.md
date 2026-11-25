# Can another instrument constrain aircraft motion?

The two stretches used in the gyro-free check have GPS positions and
accelerometer readings. A position track gives the direction of travel.
It leaves aircraft heading, pitch and bank undetermined. A measured
force direction also leaves the aircraft free to turn around that
direction. A second measurement would need to cover the same times and
constrain that freedom. [Gyro-free motion result](SHARED_GPS_MOTION_RATE_RESULT.md)

The RF04 flight file has since been acquired and verified. It covers all
443 one-second times in the selected IMU21 stretch. See the [intake result](NCAR_RF04_INTAKE.md)
for the reported channels and observed attitude changes. The catalog review
below records how the source was identified.

## What the catalogs show

| Selected stretch, UTC | Nearest timed LVIS images before and after | Other aircraft data |
| --- | --- | --- |
| IMU8, 2009-10-24 13:25:51–13:37:00 | 13:21:40.900 and 13:54:50.200 | No ILVIS0 `planedata` file listed for that date. |
| IMU21, 2011-10-12 12:05:40–12:13:02 | 11:46:00.900 and 12:47:02.700 | NCAR's one-second netCDF and NASA's text export cover 11:31–21:40 with the same attitude and GPS over the selected stretch. |

NASA's Common Metadata Repository returned zero timed image records
inside both stretches. The raw LVIS images are cataloged by day and
those entries alone cannot establish frame overlap. The Level-1A camera
times and reported orientations come from the accompanying navigation
system. A separate image-based attitude estimate would need overlapping
frames and a method that uses the image content. [IMU8 image query](https://cmr.earthdata.nasa.gov/search/granules.json?short_name=IOLVIS1A&temporal=2009-10-24T13%3A25%3A51Z%2C2009-10-24T13%3A37%3A00Z) ·
[IMU21 image query](https://cmr.earthdata.nasa.gov/search/granules.json?short_name=IOLVIS1A&temporal=2011-10-12T12%3A05%3A40Z%2C2011-10-12T12%3A13%3A02Z) ·
[LVIS image guide](https://nsidc.org/data/iolvis1a/versions/1)

The distributed NCAR file reports inertial-reference-system pitch, roll
and true heading at one sample per second. The supplied NASA text export
matches those measurements and the receiver trajectory at all 443 selected
seconds. [Measured overlap](NCAR_RF04_INTAKE.md#what-the-nasa-text-file-adds)

For the RF04 interval, NASA's timed DMS and CAMBOT collections also
returned zero image records. The day catalog lists frames from both
collections. One raw LVIS JPEG is cataloged on the correct Gulfstream V
airframe, N677F, with a day-wide time range in both its catalog record and
public sidecar. A bounded request for its first 64 KiB returned HTTP 401
with zero image bytes. Raw image overlap and camera-clock accuracy remain
unverified. [DMS time query](https://cmr.earthdata.nasa.gov/search/granules.json?short_name=IODMS1B&temporal=2011-10-12T12%3A05%3A40Z%2C2011-10-12T12%3A13%3A02Z) ·
[CAMBOT time query](https://cmr.earthdata.nasa.gov/search/granules.json?short_name=IOCAM1B&temporal=2011-10-12T12%3A05%3A40Z%2C2011-10-12T12%3A13%3A02Z) ·
[Raw image record](https://cmr.earthdata.nasa.gov/search/granules.umm_json?concept_id=G3448868543-NSIDC_CPRD) ·
[Raw image sidecar](https://data.nsidc.earthdatacloud.nasa.gov/nsidc-cumulus-prod-public/LVIS/ILVIS0/1/2011/10/12/ILVIS0_camera_55846_camera2_IMG_4411.JPG.xml)

## What that would let us test

RF04's angles describe pitch, roll and heading changes between sampled
seconds. The [averaged force check](RF04_FORCE_AVERAGE_RESULT.md) uses that
separate inertial reference alongside the gyro-free comparison.
The one-second reports leave motion within each second unresolved.
The current model comparisons still lack a measured short-timescale aircraft
motion limit independent of inertial navigation.

## Which motion information could RF04 provide?

NCAR documents the Gulfstream V's aircraft attitude source as a
Honeywell inertial reference system. The campaign example marks the
pitch, roll and true-heading channels with an 80 ms time-lag magnitude.
It also lists an applied pitch calibration. RF04's header reports 50 Hz
upstream sampling for roll and pitch and 25 Hz for heading. The channels
were distributed at 1 Hz. See the intake for the time tags used to
compare onboard measurements.
[Campaign example header](https://archive.eol.ucar.edu/raf/Projects/ICEBRIDGE/LRTdump.html) ·
[NCAR processing guide](https://ncar.github.io/aircraft_ProcessingAlgorithms/3-the-state-of-the-aircraft)

Changes in attitude between successive samples could check
whole-second motion. Within-second motion can cancel between the two
samples. Even with exact attitudes, the net angle divided by the elapsed
time only gives a lower bound on the peak rate. The sampled
[acceleration-only rate check](RECORDED_MOTION_RATE_RESULT.md) would
need independent upper limits on motion at its own times to rule out
paths that rotate too fast.

The NASA metadata search returned no
`IANCR1B` granule for that date. NSIDC identifies NCAR as the archive
for `IANCR1B`, so that metadata gap does not contradict the RF04 listing.
RF04's separate avionics pressure channel can check pressure changes.
Converting pressure changes to height also needs atmospheric and
calibration uncertainty.
[Tested RF04 intake and interpretation](NCAR_RF04_INTAKE.md) ·
[NSIDC dataset description](https://nsidc.org/data/iancr1b/versions/1) ·
[NCAR order form for RF04](https://data.eol.ucar.edu/cgi-bin/codiac/fgr_form/id=351.003) ·
[NASA aircraft-file catalog entry](https://cmr.earthdata.nasa.gov/search/granules.umm_json?concept_id=G3449174571-NSIDC_CPRD)

## Other NASA collection checks

Eight targeted NASA catalog queries for alternate attitude, pressure,
radar or timing products returned no granules in the selected intervals.
The same time queries returned LVIS records on both dates. The catalog
check covers only the listed products and their cataloged time ranges.
RF04 remains the identified outside source for the 2011 stretch.
[Exact collection queries and counts](alternate-motion-catalog.json)

## Public route and installation records

NASA's flight page identifies RF04 as the Evans Ice Stream survey
on the NCAR Gulfstream V. Both public route exports contain one line
with 8,823 three-dimensional vertices. The KMZ has no timestamp element.
Every measure value in the shapefile is marked missing. Both files
give route context. Neither supplies timestamped motion or attitude
for the seven-minute comparison. The legacy raw-data link in the
KMZ redirects to a page that returned HTTP 404.
[Flight page](https://lvis.gsfc.nasa.gov/Data/Maps/AN2011Map.html) ·
[KMZ](https://lvis.gsfc.nasa.gov/images/kmz/traj55846_LVIS.kmz) ·
[Shapefile](https://lvis.gsfc.nasa.gov/images/shape/traj55846_LVIS_SHP.zip)

The exact flight-day ILVIS0 GPS catalog returned seven `base` files, seven
`remote` files and two checksum lists under the flight's GPS prefix.
The catalog gives a day-wide time range and does not establish which,
if any, remote record is a separate onboard receiver or covers the
selected stretch. No measurement files from those entries were downloaded.
[GPS catalog query](https://cmr.earthdata.nasa.gov/search/granules.umm_json?short_name=ILVIS0&temporal=2011-10-12T00%3A00%3A00Z%2C2011-10-12T23%3A59%3A59Z&producer_granule_id%5B%5D=ILVIS0_gps_55846%2A&options%5Bproducer_granule_id%5D%5Bpattern%5D=true&page_size=40)

An earlier campaign on the same tail number documents the research
GPS antenna 3.25 m aft, 0.57 m left and 1.25 m above the static pressure
sensor. That survey did not locate the separate LVIS antenna used in
2011. The historical dimensions therefore leave the antenna-to-antenna
position in RF04 unknown. The IceBridge calibration sheet covers pressure,
temperature and related air-data channels. The campaign lists a separate
inertial performance note, but that file returned HTTP 403.
[Earlier N677F antenna record](https://archive.eol.ucar.edu/raf/Projects/TREX/DGPS.html) ·
[IceBridge calibration and instrument index](https://archive.eol.ucar.edu/raf/Projects/ICEBRIDGE/)

The downloaded KMZ and shapefile archives have SHA-256
`d005098620e92de7c8e6d93201664193bdc1408f8e4de9761afcc7c07435c412`
and `994baa5201adaae3c6423bea1d1193052abe0a6ac41933bd8dca82198d90966a`.
The shapefile check reads the optional measure array in its single
PolylineZ record. The KMZ check reads the KML line and its tags.

## What the paired recorders showed

On 20 October 2009, two onboard recorders reported different short-timescale
rates during a shared overlap. That was a separate flight from the 24
October force-direction check. An independent aircraft-motion limit
remains open. [Paired motion recordings](PAIRED_GYRO_MOTION_RESULT.md)

On 24 October, the matching pair was used to compare the original
acceleration-only direction paths with the two logged gyro streams.
Most matched intervals needed more angular travel for every candidate
than either recorder's interval allowance. The comparison puts the
single-packet acceleration assumption in question. An independent limit
on actual motion remains open. [Matched interval result](PAIRED_GYRO_INTERVAL_RESULT.md)

Quarter-second and one-second force averages clear the recorded angular
budget for all four candidates on the same 24 October intervals. The
average-based check leaves the independent physical motion limit open.
[Averaged force result](PAIRED_GYRO_AVERAGED_FORCE_RESULT.md)
