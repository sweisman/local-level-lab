# A ground receiver reference for ESA development flight 187

The one-second records from [Nuuk Museum](ESA_NKAR_GROUND_SCORE_RESULT.md)
and [permanent Nuuk](ESA_NUUK_HIGHRATE_INTAKE_RESULT.md) each match all 520
whole-second timestamps in the saved aircraft window. The source-search
details below retain the acquisition history.

## Two routes to nearby one-second observations

- **Nuuk Museum (`NKAR`).** EarthScope lists the one-second file for
  6 July 2023. Its file download requires EarthScope sign-in. SONEL lists
  the station, but its day-187 calendar reports no file. A station listing
  on SONEL does not supply the flight-day observations.
  [EarthScope day catalogue](https://data.earthscope.org/archive/gnss/highrate/1-Hz/rinex/2023/187/nkar/) ·
  [SONEL station calendar](https://www.sonel.org/spip.php?page=gps&idStation=4913)
- **Permanent Nuuk (`NUUK00GRL`).** The operator's site log shows a
  Septentrio PolaRx5 installed from September 2022 through June 2025.
  The GNET network paper describes hourly one-second raw logging on
  that receiver class. This identifies a second plausible source. The
  permanent station is about 1.01 km from the museum receiver using the
  published station coordinates. The signed-in Danish archive supplied
  the verified one-second recording for 6 July 2023.
  [Station log](https://gnss-metadata.eu/sitelog/exportlog?station=NUUK00GRL) ·
  [Network paper, §2.4](https://essd.copernicus.org/articles/18/5117/2026/#section2.4) ·
  [Danish GNSS archive](https://dataforsyningen.dk/data/4804) ·
  [Permanent station coordinates](https://www.sonel.org/spip.php?page=gps&idStation=3584)

For the permanent station, the required original observations cover
**11:49:56.5–11:58:36.5 UTC on 6 July 2023**. Request the raw hourly
file covering 11:00–12:00 UTC or a one-second RINEX export of that hour,
with the station header and carrier phase and code on both GPS bands.
The two station paths would test differences in nearby ground tracking
if both become available. Neither by itself supplies an independent
airborne antenna error bound.

The documented Dataforsyningen distribution uses implicit FTPS on port 990.
The [published RINEX path convention](https://raw.githubusercontent.com/atedstone/gnssice/master/rinex_helpers/dk_rinex_generate_list.py)
identified the daily one-second file at
`/GNSS/RINEX3/GRL/2023/187/NUUK00GRL_R_20231870000_01D_01S_MO.crx.gz`
on `ftp.dataforsyningen.dk`. Anonymous FTPS returned `530` and the
unauthenticated HTTPS download route returned `403`. The subsequent
signed-in download confirmed the filename and coverage.
[Dataforsyningen FTPS instructions](https://dataforsyningen.dk/asset/PDF/vejledninger/ftp-vejledning.pdf)

The [GFZ one-second day index](https://isdc-data.gfz.de/gnss/data/highrate/2023/187/)
listed 3,724 compressed observation files and none for NUUK, KAPI, KELY,
KSUT or NKAR. The [EarthScope one-second day index](https://data.earthscope.org/archive/gnss/highrate/1-Hz/rinex/2023/187/)
listed NKAR and none of those four other stations. These are checks of the
public mirrors. The [network operator](https://go-gnet.org/data-and-site-log)
still lists its own signed-in distribution for permanent Nuuk. The GFZ
and EarthScope index responses had SHA-256 values
`152c117dd40470f400c640804f6c563ff55d2dcd340f41b3e0a5db12878960f7` and
`0931c6dc9a8112be39286a9b2eb235bd76e10a0845db7955c0ed57a3da1bac09`, respectively.

The public NUUK log response had SHA-256
`25076e797d5bbc8f487abcb51bdc89ff6a6d11604f8184f77407b2292110ce73`.
SONEL's NKAR calendar response for station 4913 and year 2023 had SHA-256
`d3622bb02c0c2435645dae104eafa3dd46733ac4926a19b32462dd06900d4730`.
The date-filtered EPOS metadata query for permanent NUUK returned an
empty list for this date. No high-rate ground observations were acquired
in this check.

## Measurements already in hand

The permanent Nuuk station (`NUUK00GRL`) now has a verified overlap.
The SONEL 30-second file matched 17 aircraft observations. Eleven GPS
satellites stayed continuous between the four times within the shorter
test interval. This supplies the lower-rate comparison. The
[completed carrier comparison](ESA_NUUK_GROUND_PHASE_RESULT.md)
finds that adding the test displacement increases the aircraft-minus-ground
range error from 3.55 cm to 18.90 cm RMS on those 90 seconds.
[Permanent station intake](ESA_NUUK_GROUND_INTAKE_RESULT.md)

An [earlier-to-later check](ESA_NUUK_PHASE_TRANSFER_RESULT.md) found that a
partial ground correction learned from earlier observations improved range
agreement on all three later intervals. The high-rate data are needed to
test how this correction behaves at one-second spacing.

EarthScope lists a **1 Hz Nuuk Museum (`NKAR`) observation file for the
flight date, 6 July 2023**. The 43 MB compressed RINEX file and its 71 KB
summary both redirect to EarthScope sign-in. The acquired observations match
all 520 integer GPS seconds in the aircraft interval,
11:49:56.5–11:58:36.5 UTC.
`NKAR` is a separate station from the `NUUK` receiver in the earlier search.
The [one-second design check](ESA_GROUND_GRID_SCORE_RESULT.md) gives a
4.65 cm per-coordinate accuracy target for the tested score when the
sample gaps contribute negligible error and the endpoints are fixed.
The [legacy RINEX intake](ESA_NKAR_INTAKE_READY.md) records the format
and source verification.
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

The intake checked the time system, exact common epochs, dual-frequency
GPS signals and carrier lock. It also checked the aircraft's intervening
half-second reports for missing observations and lock flags.
For the two-minute test, the [one-second carrier replay](ESA_NKAR_CADENCE_RESULT.md)
puts the required correction at 9.77 mm RMS across the aircraft's retained
satellite ranges. The actual aircraft-minus-ground RMS was 8.10 mm on
the matched rows. The signed comparison and joint error budget remain
distinct from that overall RMS. Errors local to the aircraft antenna
and the full airborne prediction error still require separate evidence.
[Measured comparison](ESA_NKAR_GROUND_SCORE_RESULT.md)

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
base receiver. The authenticated flight-187 raw directory listing matched
the saved listing byte for byte (SHA-256
`7675e794c8aeceb607d7cdc238c997c13c8ce807c3b6adb4add699d1dfeeae21`).
It lists three aircraft receivers and two gravimeter directories. The
raw archive's top-level listing has only numbered flight directories.
Neither listing identifies a separate airport receiver for this flight.
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
