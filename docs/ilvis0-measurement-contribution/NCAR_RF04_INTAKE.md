# An outside motion check for the IMU21 stretch

The original **RF04 flight file for 12 October 2011** passed intake. Its
metadata identify the IceBridge Gulfstream V, N677F. It supplies all **443
one-second reports** from 12:05:40 through 12:13:02 UTC, the selected IMU21
stretch. All 443 have valid roll, pitch and true heading. [NCAR dataset](https://doi.org/10.5065/D6R49P35) ·
[RF04 order form](https://data.eol.ucar.edu/cgi-bin/codiac/fgr_form/id=351.003)

The available reference GPS, static pressure and ambient temperature channels
also cover all 443 seconds. Reference GPS status is OK throughout and the
receiver reports nine satellites at each epoch. The GPS height is relative to
mean sea level. Compare height changes with attention to the two height
references, and match time and position before interpreting receiver differences.

Over 442 consecutive report pairs, the shortest three-axis rotation had a
median of **0.059°**, a 95th percentile of **0.178°** and a maximum of
**0.332°**. Those changes are in the reported navigation frame. The header
lists upstream sampling at 50 Hz for roll and pitch and 25 Hz for heading, with
a documented −80 ms lag for all three. The pitch channel lists a +0.4°
calibration offset. Intake uses the reported values with no additional
pitch correction or time shift. This file contains one output per second.
Motion within a second can cancel
between reports, so these changes cannot bound peak aircraft rotation. Use
the separate inertial reference for a motion cross-check outside the gyro-free
model score. [Matched rotation and GPS results](RF04_MOTION_MATCH_RESULT.md) ·
[Motion-source audit](MOTION_SOURCE_AUDIT.md)

## Which channels are separate?

The campaign lists two Honeywell Laseref IV SM inertial reference systems
and a NovAtel OEM4 GPS receiver. `GGLAT`, `GGLON` and `GGALT` are the
reference receiver output. `LATC` and `LONC` blend GPS with inertial
navigation. The intake retains the receiver fields and their status.
[NCAR instrument summary](https://archive.eol.ucar.edu/raf/Projects/ICEBRIDGE/IceBridge.inst.doc) ·
[NCAR data quality report](https://archive.eol.ucar.edu/raf/Projects/ICEBRIDGE/IceBridge.QA.doc)

RF04 reports identical values for reference static pressure `PSXC` and its
input `PSFC` in this window. The separate avionics static pressure `PS_A`
can check pressure changes. Relative
height inferred from pressure would still require atmospheric and calibration
uncertainty. NCAR lists the one-second production data publicly and identifies
the raw aircraft data summary as internal. [NCAR campaign documentation](https://archive.eol.ucar.edu/raf/Projects/ICEBRIDGE/)

The file also identifies two receiver velocity sources. `GGVNS` and
`GGVEW` are north and east velocities from the reference receiver.
The avionics receiver supplies `VNS_G`, `VEW_G` and `VSPD_G`, with
its own reported UTC measurement time and status. The file lists a
−1,500 ms lag for the horizontal avionics channels and −500 ms for
the vertical channel. These are one-second output channels. Check
what timing correction was already applied before comparing them with
acceleration derived from positions. [NCAR variable definitions](https://www.eol.ucar.edu/content/raf-measured-parameter-list)

Both reference horizontal velocities are available at all 443 seconds
and the reference receiver status is OK throughout. The avionics status
field contains the file's missing-value marker in all 443 reports, and
its measurement-time field steps backward 44 times. Start the acceleration
cross-check with the reference receiver's horizontal components. The
avionics measurements need separate time and quality verification.

NCAR’s campaign report identifies the reference receiver as a NovAtel
system aided by OmniSTAR XP. The netCDF header gives 5 Hz upstream sampling
for reference speed, course and both horizontal velocity components. The
flight report leaves course precision and the order of conversion and
averaging undocumented. The [speed and course check](RF04_VELOCITY_RESOLUTION_RESULT.md)
tests the resolution directly from the saved reports.
The three raw body-rate channels described by NCAR are absent from
this file. [NCAR campaign quality report](https://archive.eol.ucar.edu/raf/Projects/ICEBRIDGE/IceBridge.QA.doc) ·
[NCAR body-rate definitions](https://ncar.github.io/aircraft_ProcessingAlgorithms/3-the-state-of-the-aircraft#raw-body-pitch-rate-s-bpitchr)

## What the NASA text file adds

The supplied `ILVIS0_planedata_55846_OIBGVrf04.asc` is 9,338,517 bytes
and matches the NASA catalog SHA-256
`05eaf2621124160c21bfba4c570cb305711a2ef13243c68440ff2327aac677b0`.
Its 36,541 rows match every NCAR timestamp from 11:31:00 through 21:40:00
UTC, exactly one second apart. In the selected 443 seconds, roll, pitch,
true heading, GPS position, ground speed and horizontal velocity all agree
with NCAR to within 0.00000051 in their recorded units. Across the full
flight, the same comparison finds one heading exception of 0.000031°.
Some derived fields, including true airspeed and wind, differ.

The agreement identifies the attitude and receiver channels as the same
one-second observations for this comparison. The text file supplies no
additional gyro, subsecond motion or independent receiver measurements.
[Exact NASA catalog entry](https://cmr.earthdata.nasa.gov/search/granules.umm_json?concept_id=G3449174571-NSIDC_CPRD) ·
[Earthdata download](https://data.nsidc.earthdatacloud.nasa.gov/nsidc-cumulus-prod-protected/LVIS/ILVIS0/1/2011/10/12/ILVIS0_planedata_55846_OIBGVrf04.asc)

The public NCAR campaign page lists the one-second netCDF and flight tracks.
The raw ADS summary is marked internal. NASA's public trajectory exports
give positions without per-vertex timestamps or attitude. If a faster
aircraft file becomes available, verify its clock, coverage over
12:05:40–12:13:02 UTC, and the source of its attitude before using it as a
separate motion measurement. [NCAR campaign catalog](https://archive.eol.ucar.edu/raf/Projects/ICEBRIDGE/) ·
[Public trajectory and installation review](MOTION_SOURCE_AUDIT.md#public-route-and-installation-records)

With both originals in `~/Downloads`, reproduce the timestamp and channel
comparison from the repository root:

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- \
  ~/venv/bin/python -c '
import csv
from datetime import datetime, timedelta
from pathlib import Path
from scipy.io import netcdf_file
from lll.ilvis0_ncar_rf04 import START, END

downloads = Path.home() / "Downloads"
with (downloads / "ILVIS0_planedata_55846_OIBGVrf04.asc").open(newline="") as stream:
    rows = list(csv.DictReader(stream))
times = [datetime.fromisoformat(r["Date"] + "T" + r["UTC"] + "+00:00") for r in rows]
selected = [i for i, t in enumerate(times) if START <= t <= END]
with netcdf_file(downloads / "RF04.20111012.113100_214000.PNI.nc", "r", mmap=False) as data:
    clock = data.variables["Time"]
    origin = datetime.fromisoformat(clock.units.decode().removeprefix("seconds since "))
    assert times == [origin + timedelta(seconds=int(t)) for t in clock[:]]
    assert all(b - a == timedelta(seconds=1) for a, b in zip(times, times[1:]))
    print(len(times), len(selected))
    for field in ("PITCH", "ROLL", "THDG", "GGLAT", "GGLON", "GGALT", "GGSPD", "GGVNS", "GGVEW"):
        errors = [abs(float(r[field]) - float(v))
                  for r, v in zip(rows, data.variables[field][:], strict=True)]
        print(field, max(errors), max(errors[i] for i in selected))
'
```

## Intake command

The verified file is `RF04.20111012.113100_214000.PNI.nc` (20,366,356 bytes).
Its SHA-256 is `31fccac2fbc36473e8d1bdb158f067c832bf04e05f8d2fd5db137eaa02039d70`.
Run from the repository root to generate the local report. Four deterministic
tests cover time gaps, missing values, heading wrap and the separate channels.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- \
  ~/venv/bin/python -m lll.ilvis0_ncar_rf04 /path/to/RF04.nc \
  --output /path/to/rf04-motion-intake.json
```

Add `--include-reference-velocity --include-reference-course` to include
the later checks’ north/east velocity, speed and course in the extract.
The combined verifier uses the sealed extracts stored with each study.
[RF04 evidence](../analysis-provenance/RF04_EVIDENCE.md)
