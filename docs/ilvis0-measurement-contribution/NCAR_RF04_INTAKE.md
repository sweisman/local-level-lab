# An outside motion check for the IMU21 stretch

NCAR lists one roughly 19 MB flight file, **RF04 on 12 October 2011**, for
the same Gulfstream V flight as the selected IMU21 stretch. Its listing covers
the complete 12:05:40–12:13:02 UTC window. The file is distributed through
NCAR's order form, which sends a download notice by email. The flight file
itself is still pending. [NCAR dataset](https://doi.org/10.5065/D6R49P35) ·
[RF04 order form](https://data.eol.ucar.edu/cgi-bin/codiac/fgr_form/id=351.003)

The intake verifies the flight and UTC clock, reports the observed overlap,
and retains roll, pitch and true heading with their timing and calibration
metadata. It can also preserve the reference GPS position and quality flags,
the separate static-pressure channels and ambient temperature. Missing values
and time gaps remain visible. Tests on generated netCDF files cover flight
identity, gaps, heading wrap and the separate sensor channels. The expected
definitions come from the campaign's RF01 example. RF04 coverage and field
availability still need checking against the actual file.
[Campaign file header](https://archive.eol.ucar.edu/raf/Projects/ICEBRIDGE/LRTdump.html)

The calculation reports the shortest rotation between successive one-second
attitude estimates in their reported frame. Faster motion could cancel before
the next report. The separate inertial reference serves as a motion check
outside the gyro-free model score. [Motion-source audit](MOTION_SOURCE_AUDIT.md)

## Which channels are separate?

The campaign lists two Honeywell Laseref IV SM inertial reference systems
and a NovAtel OEM4 GPS receiver. The RF01 example shows one complete
roll, pitch and heading set and a second-system track angle. Its `GGLAT`,
`GGLON` and `GGALT` fields are the reference receiver output. `LATC` and
`LONC` blend GPS with inertial navigation. The intake retains the receiver
fields and their status without substituting the blended fields.
[NCAR instrument summary](https://archive.eol.ucar.edu/raf/Projects/ICEBRIDGE/IceBridge.inst.doc) ·
[NCAR data quality report](https://archive.eol.ucar.edu/raf/Projects/ICEBRIDGE/IceBridge.QA.doc)

The example derives reference static pressure `PSXC` from `PSFC`. The
separate avionics static pressure `PS_A` can check pressure changes. Relative
height inferred from pressure would still require atmospheric and calibration
uncertainty. NCAR lists the one-second production data publicly and identifies
the raw aircraft data summary as internal. [NCAR campaign documentation](https://archive.eol.ucar.edu/raf/Projects/ICEBRIDGE/)

NSIDC also lists a 9,338,517-byte ASCII aircraft position, attitude and motion
file, `ILVIS0_planedata_55846_OIBGVrf04.asc`, for the same date and aircraft
tail number, N677F. Its direct download requires an Earthdata sign-in. Its
relationship to the NCAR export and its sample rate remain unverified. The
catalog gives SHA-256
`05eaf2621124160c21bfba4c570cb305711a2ef13243c68440ff2327aac677b0`.
[Exact NASA catalog entry](https://cmr.earthdata.nasa.gov/search/granules.umm_json?concept_id=G3449174571-NSIDC_CPRD) ·
[Earthdata download](https://data.nsidc.earthdatacloud.nasa.gov/nsidc-cumulus-prod-protected/LVIS/ILVIS0/1/2011/10/12/ILVIS0_planedata_55846_OIBGVrf04.asc)

## Intake command

When the original is available, run from the repository root. The intake
supports classic and 64-bit-offset netCDF and writes a hash-bound local report.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- \
  ~/venv/bin/python -m lll.ilvis0_ncar_rf04 /path/to/RF04.nc \
  --output /path/to/rf04-motion-intake.json
```
