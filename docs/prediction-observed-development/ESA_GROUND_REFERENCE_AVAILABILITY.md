# A ground receiver reference for ESA development flight 187

The permanent Nuuk station (`NUUK00GRL`) now has a verified overlap.
The SONEL 30-second file matched 17 aircraft observations. Eleven GPS
satellites stayed continuous between the four times within the shorter
test interval. This offers a lower-rate check while the Nuuk Museum
observations are pending. The [completed carrier comparison](ESA_NUUK_GROUND_PHASE_RESULT.md)
finds that adding the test displacement increases the aircraft-minus-ground
range error from 3.55 cm to 18.90 cm RMS on those 90 seconds.
[Permanent station intake](ESA_NUUK_GROUND_INTAKE_RESULT.md)

An [earlier-to-later check](ESA_NUUK_PHASE_TRANSFER_RESULT.md) found that a
partial ground correction learned from earlier observations improved range
agreement on all three later intervals. The high-rate data are needed to
test how this correction behaves at one-second spacing.

EarthScope lists a **1 Hz Nuuk Museum (`NKAR`) observation file for the
flight date, 6 July 2023**. The 43 MB compressed RINEX file and its 71 KB
summary both redirect to EarthScope sign-in. Exact coverage of the aircraft
interval, 11:49:56.5–11:58:36.5 UTC, still needs to be read from the file.
`NKAR` is a separate station from the `NUUK` receiver in the earlier search.
The [one-second design check](ESA_GROUND_GRID_SCORE_RESULT.md) gives a
4.65 cm per-coordinate accuracy target for the tested score when the
sample gaps contribute negligible error and the endpoints are fixed.
The [legacy RINEX intake](ESA_NKAR_INTAKE_READY.md) is tested and ready
to check the actual flight overlap when the original arrives.
[Station-day catalogue](https://data.earthscope.org/archive/gnss/highrate/1-Hz/rinex/2023/187/nkar/) ·
[EarthScope station registry](https://www.unavco.org/data/gps-gnss/data-access-methods/dai1/recent.php) ·
[Aircraft time window](ESA_PRECISE_GPS_SUPPORT_RESULT.md)

The catalogue lists `nkar1870.23d.Z` and `nkar1870.23S` with archive dates
of 31 March 2025. The public catalogue response had SHA-256
`3a16259d26279f67052eeaa9a0386f73f658c615225120e97df3c00c7c58214b`.
The corresponding raw directory showed no files. The EPOS station-specific
lists for `NUUK` and `KAPI` returned newer entries and did not verify the
requested day. A day listing does not establish an unbroken observation arc.
[Compressed observations](https://data.earthscope.org/archive/gnss/highrate/1-Hz/rinex/2023/187/nkar/nkar1870.23d.Z?type=file) ·
[Observation summary](https://data.earthscope.org/archive/gnss/highrate/1-Hz/rinex/2023/187/nkar/nkar1870.23S?type=file) ·
[NUUK catalogue](https://doi.org/10.60888/EPOS-GNSS-NUUK00GRL) ·
[KAPI catalogue](https://doi.org/10.60888/EPOS-GNSS-KAPI00GRL)

With the original file available, verify the time system, exact common epochs,
dual-frequency GPS signals and carrier lock before using it as a ground
reference. The saved aircraft stream reports twice a second. A complete 1 Hz
ground stream on the same GPS clock would offer 520 exact pairs in this
window. A software test verifies that the pairing also checks the aircraft's
intervening half-second record for missing observations and lock flags.
For the two-minute test, the [one-second carrier replay](ESA_NKAR_CADENCE_RESULT.md)
puts the required correction at 9.77 mm RMS across the aircraft's retained
satellite ranges. The ground observations are needed to compare with that
signal scale.
A matched comparison could constrain shared satellite and nearby
atmospheric errors. Errors local to the aircraft antenna and the full
airborne prediction error still require separate evidence.

The BKG high-rate archive also supplied a public, more distant ground control
at Qaqortoq. All 121 seconds of the two-minute window matched, with five or
more common GPS satellites in all 120 intervals. The station is 456–458 km
from the saved aircraft path. The Kangerlussuaq `KLSQ00GRL` archive for the same
date has twelve quarter-hour files and no overlap with this window.
[Qaqortoq intake](ESA_QAQ_GROUND_INTAKE_RESULT.md) ·
[BKG high-rate day listing](https://igs.bkg.bund.de/root_ftp/IGS/highrate/2023/187/)

## Earlier reference search

Three Greenland stations lie within 75 km of the saved 400/120 comparison
window. The public daily observation indexes checked for 6 July 2023 did
not list their station IDs. The campaign separately describes an airport
base receiver, whose observations for this flight are still unverified.
[Earlier archive check](ESA_PRECISE_GPS_SUPPORT_RESULT.md#ground-references)

The follow-up verified that `KSUT` began operating after the flight.
A separate fixed receiver in Reykjavík matches the aircraft's later
stop. That result gives a ground control in Iceland while Greenland
availability remains open. [KSUT station history](https://go-gnet.org/station-summary/ksut) ·
[Reykjavík source check](ESA_FIXED_REFERENCE_PAIR_RESULT.md)

| Ground station | Horizontal distance across the window |
| --- | ---: |
| Nuuk `NUUK` | 13.2–41.3 km |
| Nuuk `KSUT` | 20.1–55.4 km |
| Kapisillit `KAPI` | 42.8–74.9 km |
| Kangerlussuaq `KELY` | 315.2–325.0 km |

Distances use the archived 1,039 carrier-path positions and a 6,371 km
spherical radius. This distance calculation serves archive sourcing.
[Saved carrier path](ESA_CARRIER_PHASE_CONTINUOUS_RESULT.md) ·
[Official station coordinates](https://go-gnet.org/gnet-coordinates)

The search checked the station IDs in the listed filenames at the BKG IGS,
BKG EUREF, EPOS and EarthScope daily indexes. The ROB historical data API
also returned an empty file list for KELY on day 187. The primary Greenland
distribution requires sign-in. These public indexes can miss files that
are available through the primary distribution or other channels.
[BKG IGS](https://igs.bkg.bund.de/root_ftp/IGS/obs/2023/187/) ·
[BKG EUREF](https://igs.bkg.bund.de/root_ftp/EUREF/obs/2023/187/) ·
[EPOS](https://datacenter.gnss-epos.eu/RINEX3/30s/2023/187/) ·
[EarthScope](https://data.earthscope.org/archive/gnss/rinex/obs/2023/187/) ·
[ROB daily file query](https://gnss.be/api/v1/epn/distribution/KELY00GRL/2023/187/3) ·
[Greenland data access](https://go-gnet.org/data-and-site-log)

A ground record would test part of the error shared by the airborne
receivers, such as errors in satellite clock and orbit products. Its
use would require checking the overlap, sampling cadence and available
signals. Aircraft antenna and tracking errors need their own checks.
