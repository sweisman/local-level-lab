# Other sources for a flight comparison

A confirmation recording needs raw gyroscope and accelerometer data,
documented timing and calibration, and a separate position or motion
reference. The aircraft must also cover enough distance on usable legs.
A reference made with the gyro under test cannot independently check that
gyro. This screen used catalog records and one small public sample.

| Candidate | What is available | Practical use |
| --- | --- | --- |
| Swiss IGN Flight 6 | Two raw 500 Hz NavChip inertial streams, receiver observations and a GPS-only kinematic solution. The sampled flight is a low-speed drone survey over a short corridor. [Archive](https://zenodo.org/records/4705381) | Useful for testing ingestion and comparing recorders. Set aside for confirmation at the observed speed and instrument quality. |
| Porto Galileo flight campaign | A Cessna carried two navigation systems, including a 200 Hz LN200, and two roof antennas. The paper describes antenna offsets and a receiver-only solution. [Campaign study](https://doi.org/10.3390/rs14143414) | The strongest hardware match in this screen. A public raw-data download was not located. Access to those files and verification of long usable legs remain open. |
| East Antarctica ICECAP | The archive lists stabilized gravity observations and a separate Javad receiver. The level-zero distribution requires arranging access with the archive. [Data Center record](https://www.usap-dc.org/view/dataset/602073) | Could supply a gravity or receiver check. The public documentation checked here does not establish a full set of raw aircraft-axis angular observations. |
| NOAA GRAV-D and BAS Thwaites | Both programs collected airborne navigation data. The public releases examined provide processed airborne gravity. [NOAA release](https://geodesy.noaa.gov/web/GRAV-D/data_products.shtml) · [BAS release](https://data.bas.ac.uk/full-record.php?id=GB%2FNERC%2FBAS%2FPDC%2F01323) | The released products do not supply the original gyro stream needed for this comparison. |

## What the public Swiss sample showed

Seven byte-range requests transferred **409,859 bytes** from the
4,085,920,667-byte archive. The full extracted GPS-only member passed its
ZIP checksum. It contains 13,578 position reports, normally 0.1 seconds
apart, with two intervals of 0.3 seconds. The raw prefixes contain 9,279
and 9,103 complete observations and advance exactly 0.002 seconds per
sample. Those prefixes begin before takeoff. Full inertial coverage and
alignment remain unverified. [Archive file listing](https://zenodo.org/records/4705381/preview/ign6XL.zip?include_deleted=0)

The portion of the GPS solution between the documented takeoff and
touchdown spans about 21.4 minutes. It covers 17.0 km of total horizontal
path at a median ground speed of 45.7 km/h. Distance is the sum of local
horizontal displacements between receiver reports. The total includes
repeated passes and turns in a 2 km corridor. At that median speed a globe
predicts only about 0.41°/h of turning due to curvature. The flight's
instrument notes list a nominal gyro bias of 12°/h. These source and
geometry checks give no basis to expect this recording to resolve
curvature with the current method.

The byte ranges below are inclusive and refer to `ign6XL.zip`. HTTP 206
and the exact content ranges were checked. The complete members were
decoded using their central-directory lengths and checked against their
ZIP CRCs. The two raw prefixes were used only for the format and cadence
check.

| Range | Contents |
| --- | --- |
| 4085855110–4085920666 | ZIP directory and end record |
| 112855229–112856228 | Inertial channel notes |
| 4085876089–4085877058 | Flight and installation notes |
| 4085873818–4085876077 | Archive overview |
| 4085643257–4085852256 | GPS-only trajectory |
| 80215089–80280624 | First raw inertial stream prefix |
| 96521869–96587404 | Second raw inertial stream prefix |

The extracted GPS-only `AntennaPos_WGS84.txt` has SHA-256
`0bf466ba04ee397f59b951ec6e94b6278f3166825cc07e9f1bec436fa0a3a0e2`.
The screen produced no new Earth-model fits. No reserved ESA recordings
were opened. A future candidate should first pass a one-flight intake
that verifies separate motion or position evidence, exact overlap, and
usable flight geometry before any wider acquisition.
