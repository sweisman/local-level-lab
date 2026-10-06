# A possible real airborne test

NASA's [IceBridge LVIS archive](https://nsidc.org/data/ilvis0/versions/1) contains measurements
taken aboard aircraft over Greenland, Antarctica and Alaska. The
[Level-0 user guide](https://nsidc.org/sites/default/files/ilvis0-v001-userguide_1.pdf)
lists raw IMU files labeled `applanix` or `gyro`, GPS files, camera images, and aircraft position,
attitude and motion files. IMU data can be binary or text, and different instruments can have
separate files. The documented coverage is April 2009 through September 2017.

These are promising data for testing model discrimination with a real airborne IMU. That is a
proposed use, not a result: the supplied IPUTI0 sample contains navigation outputs, and a
subsequent ILVIS0 sample contains time-tagged IMU payloads whose physical decoding is pending.
The instrument differs from the WT901, so a successful test would not establish WT901 accuracy,
drift or automatic-zero behavior.

Start with one small IMU sample and its matching GPS data, selected by date and flight geometry
before looking at the gyro result. Confirm that it contains physical gyro rates or angular
increments, establish units and axis signs, and check sample times, time scale and gaps.
Identify which instrument supplied each stream and how its axes relate to the aircraft.
Inspect calibration, applied corrections and available preflight/postflight stationary periods.
The overview guide does not provide enough detail to establish a decoder or measurement model.

Raw gyro observations are the desired input. Corrected position or attitude can help inspect
motion, but navigation software may already incorporate Earth rotation or curvature. That
processing must be traced before treating its output as independent evidence for those effects.
Any subtraction of Earth rate, drift filtering or automatic zeroing in the recorded gyro must
also be understood. Unverified corrections can erase or manufacture the distinction being tested.

Once the measurements are understood, use the route and independently reconstructed orientation
to predict all three models. Check globe/disc and rotation separation separately under plausible
instrument drift and aircraft uncertainties. Keep exclusions, abstentions and disagreements;
survey flights can maneuver frequently and a permanently mounted IMU lacks the passenger's
deliberate reversals. Useful geometry cannot be assumed from the archive's scientific purpose.
This would be a separate development study, with no reuse of synthetic calibration thresholds.

The [data access page](https://nsidc.org/data/ilvis0/versions/1) says downloads require a free NASA
Earthdata account. No credentials have been inspected or requested, and no bulk download is
planned. Obtain a small documented sample and its format specification before budgeting
processing or a larger empirical study. Cite the dataset DOI and the exact subset used.

## Catalog inspection and a second source

### Time-tagged ILVIS0 sample now available

The supplied `ILVIS0_gyro_54935_atm_applanix_14Apr09.013` is a 13,086,748-byte Applanix log.
It contains 132,444 time-tagged IMU packets at approximately 200 Hz over 662.226 seconds.
All 143,471 outer packet checksums pass, with no unframed bytes or IMU gaps above 7.5 ms.
The log identifies AV-510 VER5, firmware04.60, ICD15.00 and IMU8. The compatible public
2014 V6 documentation confirms the container, but does not define the 24-byte IMU payload's
physical scales and axes. Exact payload bytes remain opaque; no units or rate/increment
interpretation have been invented.

The same log contains 662 fused navigation records and a primary receiver stream with 660
valid GGA positions, 660 VTG sentences and 660 ZDA date/time sentences. Reassembly recovers
messages split across packet boundaries. ZDA confirms 14 April 2009, and the trajectory is
southbound over Greenland. Navigation shows a climb and maneuvers, so the entire segment
is not a qualified level-cruise window. Timestamps are preserved; sensor latency and lever
arms remain unverified. GPS is already present, so a separate GPS download is unnecessary
for initial inspection.

The [preserved sample notes](airborne-sample-ilvis0/README.md) describe the compressed original,
timed opaque IMU table, navigation table, receiver stream and provenance. Two focused checks
pass. No physical gyro decoder, main-pipeline import or Earth-model decision exists.

The next task is obtaining an IMU8 definition or an independent physical export with
documented units, axes and processing. A precise documentation request is:

> For ILVIS0 file ILVIS0_gyro_54935_atm_applanix_14Apr09.013, recorded by AV-510 VER5,
> firmware 04.60/ICD15.00/IMU8, what is the 24-byte Group 4 payload layout? Please identify
> gyro/accelerometer field order, units and scale factors, signed representation, axis
> directions, whether observations are rates or increments, integration intervals and
> timestamp conventions. What calibration, Earth-rate subtraction, filtering or other
> corrections are already applied? Is a documented export of independent gyro measurements
> available?

This is a saved draft; no message has been sent. Additional measurements are unnecessary
until the format question is resolved.

### First supplied measurement sample

The user supplied five IPUTI0 files: `ASB_JKB0a_GL0017a_AVNcp1.bxds`, its `.ct` clock file,
and the AVNcp1, AVNcp2 and clock format descriptions. The binary contains both message 3500
(system status) and message 3501 (navigation solution), despite its AVNcp1 filename. The
descriptions specify position, three velocity components, pitch, roll and heading; they
contain no raw angular-rate or angular-increment fields. This sample therefore does not
provide an independent gyro discriminator. Other archive streams have not been ruled out.

The clock spans 1,525.995 seconds, about 25½ minutes, at approximately one entry per second.
Its approximate wall-clock labels run from 07:31:49.09 to 07:57:14.93 on 1 January 2010;
their timezone is unverified. Horizontal speed ranges from 69.51 to 93.69 m/s, consistent
with an airborne survey segment. Those navigation outputs can inform aircraft-motion studies
once timing and processing are understood.

The inspection recovered 1,527 packets of each kind with zero additive checksum residues.
One apparent navigation header at byte 10,800 failed the payload checksum; searching inside
that candidate recovered valid packets beginning 11 bytes later. Those 11 unframed bytes
remain in the preserved original. Their cause is unknown. Nothing was repaired or interpolated.
The little-endian field interpretation and additive checksum convention are inferred from the
sample; the supplied descriptions establish fixed-point scales but do not resolve every
interface detail. The 64-bit time-tag representation, epoch, clock-to-packet alignment and
status bit meanings remain unverified. No guessed timestamps enter the decoded table.

All five originals, hashes, the exploratory navigation table and the inspection record are
preserved in `airborne-sample-iputi0/`. The [sample notes](airborne-sample-iputi0/README.md)
give the reproducible command and limits. Three focused decoder checks passed, including
recovery inside a failed packet candidate, signed scaling, truncation and relative clock units.
No Earth-model decision or full-pipeline fit was run. Differentiating the navigation orientation
would still produce a navigation-derived quantity, not the missing independent gyro stream.

### Earlier public metadata checks

The public catalog now confirms individual gyro files in ILVIS0. A bounded request for the
first 64 KB of `ILVIS0_gyro_54935_atm_applanix_14Apr09.013` returned a login redirect and zero
measurement bytes. The first catalog page includes both ATM and LVIS Applanix logs of roughly
12.5 reported MB. Files for different instruments must not be mixed merely because they share
a day. The catalog gives day-wide intervals, not verified sample times or flight overlap.

The supplied [alternative record](https://cmr.earthdata.nasa.gov/search/concepts/C1386246599-NSIDCV0.html)
identifies a different collection, rather than another entry for ILVIS0:

| Collection | Airborne source | What is confirmed |
|---|---|---|
| [ILVIS0](https://nsidc.org/data/ilvis0/versions/1) | LVIS support instruments, including Applanix IMUs | Raw IMU/GPS files exist; binary payload interpretation still needs confirmation. |
| [IPUTI0](https://nsidc.org/data/iputi0/versions/1) | Systron Donner MMQ-G on a Basler BT-67 over Antarctica | Text readings include position, velocity, pitch, roll and true heading; raw gyro channels remain unconfirmed. |

IPUTI0 covers 2009–2010. Its published download directory also redirected to Earthdata login;
no directory listing or measurement sample was obtained. Its title contains “raw,” but the
listed orientation outputs alone do not establish that independent angular-rate measurements
are present. These could still help characterize real aircraft motion if their processing is
understood. They must not be counted as an empirical gyro discriminator merely from the title.

The manufacturer’s [POS AV V6 interface document](https://asapdata.arc.nasa.gov/share/ASF_Applanix/POSv6_User_ICD.pdf)
offers a format lead for ILVIS0. It separates the navigation solution from IMU packets,
including groups 4 and 10002. It leaves raw IMU payload formats unpublished, citing export
restrictions. Knowing packet boundaries therefore does not provide sensor scaling and axes.
It is a 2014 document and has not been matched to the 2009 log’s hardware or firmware.
No decoder has been inferred from it. A documented instrument-specific format or an export
preserving physical angular increments/rates is needed, with all corrections identified.

Four public metadata responses are preserved as compressed originals in `airborne-metadata/`:
`ilvis0-collections.json.gz`, `ilvis0-granules.json.gz`, `ilvis0-gps-granules.json.gz`, and
`iputi0-collection.json.gz`. `analysis/tests/review_airborne_sources.py` inventories only these
explicit files and records their query URLs and hashes in `airborne-catalog-review.json`.
That review preserves the observed access failures; reproducing it does not retry downloads.
Authentication response bodies, redirect parameters and credentials are not stored in the repo.

## Resume after Earthdata registration

The user has created an Earthdata account. Complete any email verification and sign in through
NASA in a browser. Browser authentication is not shared with the project's download tools.
No credentials have been requested or inspected.

For ILVIS0, use [Earthdata Search](https://search.earthdata.nasa.gov/search/granules?p=C3162704221-NSIDC_CPRD)
to find `ILVIS0_gyro_54935_atm_applanix_14Apr09.013`, dated 14 April 2009, as a modest format
sample. The catalog provides a [direct sample download](https://data.nsidc.earthdatacloud.nasa.gov/nsidc-cumulus-prod-protected/LVIS/ILVIS0/1/2009/04/14/ILVIS0_gyro_54935_atm_applanix_14Apr09.013)
of about 12.5 MB. This exact file is now supplied and inspected; further copies are unnecessary.
Tool authentication has not been established or used. Another cataloged option is
`ILVIS0_gyro_54935_lvis_applanix_POSAV.031`; it belongs to
the LVIS instrument rather than ATM. Inspect one log first. The 2009 day is chosen for file
inspection, not because its gyro results favor a model. Establish actual timestamps and
instrument identity before choosing companion GPS or a scientific analysis window.

For IPUTI0, open the [published directory](https://daacdata.apps.nsidc.org/pub/DATASETS/ICEBRIDGE/IPUTI0_UTIGIMUraw_v01/)
while signed in. The supplied AVNcp1/AVNcp2 sample and format descriptions have now been
inspected: these are binary status/navigation packets, with no raw gyro channels. Obtain
documentation for a separate raw-sensor stream if one exists; additional files with these
same message layouts would supply more aircraft-motion data rather than the missing gyro
measurement. The supplied ILVIS0 sample now establishes a timed IMU stream; its physical
payload definition remains the next requirement.
