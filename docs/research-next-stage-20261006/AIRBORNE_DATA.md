# Real airborne IMU data: inspection and follow-up

**Current findings:** the completed 53-stretch study favors globe in 12 stretches and
flat in none; all 12 also favor rotation. The other 41 lack finished calculations, rather
than showing equal support for flat. See the [findings](../ilvis0-highspeed-segments-20261008/FINDINGS.md).
The six-recording pilot is also complete. A separately frozen
[12-fit solver trial](../ilvis0-solver-trial-20261010/README.md) is running to improve
numerical completion without changing the physical assumptions.

This guide preserves the initial inspection and later development sequence. Statements
about stages with no Earth-model fit describe their status at the time, not the current analysis.


NASA's [IceBridge LVIS archive](https://nsidc.org/data/ilvis0/versions/1) contains measurements
taken aboard aircraft over Greenland, Antarctica and Alaska. The
[Level-0 user guide](https://nsidc.org/sites/default/files/ilvis0-v001-userguide_1.pdf)
lists raw IMU files labeled `applanix` or `gyro`, GPS files, camera images, and aircraft position,
attitude and motion files. IMU data can be binary or text, and different instruments can have
separate files. The documented coverage is April 2009 through September 2017.

These survey-grade data now supply real airborne model comparisons. The initial
supplied IPUTI0 sample contains navigation outputs, and a
subsequent ILVIS0 sample contains time-tagged IMU increments whose physical decoding was
independently cross-checked on 7 October 2026. Applied corrections remain unresolved.
The instrument differs from the WT901, so a successful test would not establish WT901 accuracy,
drift or automatic-zero behavior.

The completed [archival observation check](../ilvis0-observation-20261007/README.md) now
prepares raw increment summaries and tests route separation without using fused attitude
or gyro rates as observations. One of the six routes retains predicted globe-versus-disc
separation after constant/linear bias removal under idealized independent motion correction.
This is a design diagnostic; independent processing, aircraft-motion constraints and bounded
calibration uncertainty still needed a joint raw-IMU/GPS measurement model at that stage.
No Earth fit had run then; the joint model and completed studies followed.

The [joint forward model](../ilvis0-forward-20261007/README.md) is now implemented and
controlled motion checks pass. Its six-file preparation retains full-rate finite rotations,
rotated acceleration and actual GPS endpoint timing. The
[bounded estimator controls](../ilvis0-estimator-20261007/README.md) now recover known nuisance
quantities and detect orientation/bias ambiguity. Actual processing, clock, calibration and
validated receiver covariance remain unsupported; no observed Earth fit has run. Six GPS summaries
show heights of roughly 6–12 km and ground speeds of 480–940 km/h in the prepared stretches.
High-altitude fast flight is common here; do not assume every lidar recording is low and slow.
The [receiver audit](../ilvis0-processing-v2-20261007/README.md) now decodes nearly3,000
receiver positions with reported error estimates, and reassembles raw satellite-survey
record envelopes. This advances trajectory uncertainty without using fused IMU/navigation
outputs. It does not yet calibrate temporal covariance or establish Group4 processing.

The [satellite-measurement audit](../ilvis0-gnss-v2-20261007/README.md) now decodes
19,699 epochs and 603,603 signal measurements, plus 326 GPS ephemeris packets. All six
source/record checks reproduce; 31 focused tests pass. GPS orbit geometry exposes 29
zero-angle reports for one satellite; those measurements remain preserved. The existing
files supply 5–10Hz receiver observations. No position/Earth fit or independently calibrated
covariance claim followed from that decoding stage.

The subsequent [GPS-only reconstruction](../ilvis0-position-20261007/README.md) now solves
all 2,968 preselected epochs under two fixed methods; all 5,936 primary solves and 24
displaced-start checks converge. It uses recorded GPS ranges and broadcast orbits under
conventional GPS geometry, with explicit satellite-clock, signal-time and atmospheric
corrections. It uses no fused navigation. Differences from the same receiver's position
reports are on the scale of metres and are correlated across time; they do not establish
independent accuracy. Formal covariance is not calibrated. Twenty-eight focused tests pass.
All232originals remain and no Earth fit ran.

A [correlated GPS-error sensitivity check](../ilvis0-gps-sensitivity-20261007/README.md)
now evaluates fixed assumptions over the same recordings. Persistent offsets and drift
survive position averaging; long-window acceleration precision can conceal real brief
corrections. No smoothing interval or scientific acceptance rule was chosen. Twenty-three
focused tests pass. The assumed error grid is not calibrated accuracy.
The [joint IMU/GPS controls](../ilvis0-correlated-controls-20261007/README.md) now carry
full covariance into five analytic calibration/timing fixtures. They report precision
separately from noiseless recovery and preserve offset/drift ambiguities. Thirty-three
distinct focused tests pass. These translation controls do not characterize gyro hardware,
resolve Group4 processing or establish real instrument bounds. Supported IMU processing,
calibration, mounting and timing constraints remain necessary before measured Earth fitting.

The [longer rotational controls](../ilvis0-excitation-20261007/README.md) now compare
2/20/60-second analytic records, including a one-second0.1deg pitch correction. All18
trajectory checks and4gyro-bias/timing recovery checks pass;11focused tests pass. Duration
helps local precision but does not make the tiny correction a reliable joint calibration.
The [instrument evidence matrix](../ilvis0-excitation-20261007/INSTRUMENT_EVIDENCE.md)
records supported units/settings and the remaining legacy IMU6processing/calibration/clock
questions. These remain hypotheses, not resolved by public modern packet documentation
or good noiseless recovery. No observed Earth fit has run.
The [information stability diagnostics](../ilvis0-information-20261007/README.md)
compare four central derivative steps on the same18fixtures. They report smooth
information relative to declared fixture bounds and preserve weak/null directions;
an artificial reference penalty is explicitly distinguished from measured calibration
or a confidence interval. Covariance sensitivity and numerical step stability are
reported separately. The archival fitting gate is unchanged.
The [instrument documentation review](../ilvis0-instrument-evidence-20261007/README.md)
now finds a primary published association between POS AV510/IMU-6 and tactical-grade
Litton-200 hardware. That supports the family inference; exact installed variants
and independent calibration/correction bounds remain unknown. It preserves six
cached source/configuration identities and prepares unsent questions for the exact
firmware/ICD revisions. Manufacturer descriptions identify a navigation correction
stage but not the legacy Group4 logging tap. No generic scale table or performance
number has been assigned to these bytes.
The [legacy-record search](../ilvis0-legacy-records-20261008/README.md) obtained no
manual/calibration record matching the three V5 revisions. NSIDC's current guide
supports raw, unprocessed Level-0 archive provenance, without specifying onboard
Group4 corrections. An inquiry has since been sent and NSIDC is contacting the producers.
[Modeling of the six recordings](../ilvis0-exploratory-20261008/README.md) proceeded
with stated processing and calibration allowances; the completed pilot and larger study
followed. Analysis does not pause while those additional records are sought.

Start with one small IMU sample and its matching GPS data, selected by date and flight geometry
before looking at the gyro result. Confirm that it contains physical gyro rates or angular
increments, establish units and axis signs, and check sample times, time scale and gaps.
Identify which instrument supplied each stream and how its axes relate to the aircraft.
Inspect calibration, applied corrections and available preflight/postflight stationary periods.
The overview guide does not provide enough detail to establish a decoder or measurement model.

Raw gyro observations are the desired input. Corrected position or attitude can help inspect
motion, but navigation software may already incorporate Earth rotation or curvature. That
processing must be traced before treating its output as independent evidence for those effects.
Ordinary noise filtering can preserve slow turning. Earth-rate subtraction or automatic
zeroing can remove it; these are different operations. Neither a "raw" archive label nor
a successful fit proves the absence of onboard corrections. The logged stream and matched
processing cases, rather than the word "filtered" alone, determine what can be tested.

Once the measurements are understood, use the route and independently reconstructed orientation
to predict all three models. Check globe/disc and rotation separation separately under plausible
instrument drift and aircraft uncertainties. Keep exclusions, abstentions and disagreements;
survey flights can maneuver frequently and a permanently mounted IMU lacks the passenger's
deliberate reversals. Useful geometry cannot be assumed from the archive's scientific purpose.
This would be a separate development study, with no reuse of synthetic calibration thresholds.

The [data access page](https://nsidc.org/data/ilvis0/versions/1) says downloads require a free NASA
Earthdata account. The `.013` acquisition workflow now catalogs the archive and checks a
small cross-date batch before full acquisition. Authentication is confined to Earthdata; no
credentials are recorded in evidence. Cite the dataset DOI and the exact subset used.

## Catalog inspection and a second source

### Time-tagged ILVIS0 sample now available

This is professional airborne survey hardware: the reference identifies a 200 Hz POS AV
510/IMU8, likely an LN200ROM-family fiber-optic unit. Exact sensor identity is inferred, and
published integrated-system performance must not be treated as measured raw-gyro accuracy.
The [instrument summary](../ILVIS0.md#instrument-quality) gives the sources and qualifications.

The supplied `ILVIS0_gyro_54935_atm_applanix_14Apr09.013` is a 13,086,748-byte Applanix log.
It contains 132,444 time-tagged IMU packets at approximately 200 Hz over 662.226 seconds.
All 143,471 outer packet checksums pass, with no unframed bytes or IMU gaps above 7.5 ms.
The log identifies AV-510 VER5, firmware04.60, ICD15.00 and IMU8. The compatible public
2014 V6 documentation confirms the container, but does not define the 24-byte IMU payload's
physical scales and axes. The initial inspection preserved the payload as opaque. Subsequent
empirical validation identifies six little-endian signed int32 increments: velocity X/Y/Z
followed by angle X/Y/Z, with scales `2^-14 m/s/count` and `2^-18 rad/count`. All axes/signs
and independent scale fits pass the engineering checks, including chronological holdouts.
This is empirical support, not an authoritative manufacturer scale table.

The same log contains 662 fused navigation records and a primary receiver stream with 660
valid GGA positions, 660 VTG sentences and 660 ZDA date/time sentences. Reassembly recovers
messages split across packet boundaries. ZDA confirms 14 April 2009, and the trajectory is
southbound over Greenland. Navigation shows a climb and maneuvers, so the entire segment
is not a qualified level-cruise window. Timestamps are preserved; sensor latency and lever
arms remain unverified. GPS is already present, so a separate GPS download is unnecessary
for initial inspection.

The [preserved sample notes](airborne-sample-ilvis0/README.md) describe the compressed original,
timed opaque IMU table, navigation table, receiver stream and provenance. Two focused checks
passed for the original inspector. The separate streaming decoder and validation workflow
now produce physical increments while preserving the six original integers. The original
artifacts and inspector remain historical evidence. No main scientific-pipeline import or
Earth-model decision exists. The reference has no qualifying 60-second level-flight window
under the geometry-only acquisition rule; its new bulk derivative files were discarded after
recording the result. The supplied original and historical corpus were not deleted.

The remaining documentation task concerns processing, mounting and timing, rather than a
prerequisite to recovering the increments. The earlier unsent request is retained below:

> For ILVIS0 file ILVIS0_gyro_54935_atm_applanix_14Apr09.013, recorded by AV-510 VER5,
> firmware 04.60/ICD15.00/IMU8, what is the 24-byte Group 4 payload layout? Please identify
> gyro/accelerometer field order, units and scale factors, signed representation, axis
> directions, whether observations are rates or increments, integration intervals and
> timestamp conventions. What calibration, Earth-rate subtraction, filtering or other
> corrections are already applied? Is a documented export of independent gyro measurements
> available?

This is a saved draft; no message has been sent. Additional `.013` files are now useful for
cross-file scale/layout checks and flight-window discovery. See the [acquisition guide](../ILVIS0.md).

Subsequent work on six IMU6 logs found [recorded installation angles and a clock-related
rate-conversion discrepancy](../ilvis0-installation-clock-20261007/README.md). The angle
candidates explain the relative axis changes. A fixed 200 Hz period makes all six acceleration
checks pass, while one gyro holdout narrowly fails. Legacy setting fields remain inferred,
and the physical integration clock and onboard corrections are not independently established.
These results refine the decoder investigation; they do not supply an Earth-model result.

### First supplied measurement sample

The available IPUTI0 sample consists of five files: `ASB_JKB0a_GL0017a_AVNcp1.bxds`, its `.ct` clock file,
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
| [ILVIS0](https://nsidc.org/data/ilvis0/versions/1) | LVIS support instruments, including Applanix IMUs | Two IMU8 configurations reproduced on two dates each; four candidate files provide about 32 minutes with supported units. Other configurations and onboard corrections remain unresolved. |
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

## Earthdata access

Earthdata downloads require an account and any applicable email verification. Browser
authentication is separate from the project's download tools. Use the
[acquisition guide](../ILVIS0.md) for local authentication; do not publish credentials.

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
processing and cross-configuration interpretation remain open, while the tested IMU8 physical
increment definition is now empirically supported.
