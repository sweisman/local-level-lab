# An outside motion check for the IMU21 stretch

NCAR lists one roughly 19 MB flight file, **RF04 on 12 October 2011**, for
the same Gulfstream V flight as the selected IMU21 stretch. Its listing covers
the complete 12:05:40–12:13:02 UTC window. The file is distributed through
NCAR's order form, which sends a download notice by email. The flight file
itself is still pending. [NCAR dataset](https://doi.org/10.5065/D6R49P35) ·
[RF04 order form](https://data.eol.ucar.edu/cgi-bin/codiac/fgr_form/id=351.003)

The intake verifies the flight and UTC clock, reports the observed overlap
and retains the individual roll, pitch and true heading samples. It keeps
the published timing-lag and calibration metadata, skips missing values and
does not fill gaps. It can retain reference GPS position and static pressure
for separate comparison when those variables are present. Three tests on
generated netCDF files passed, covering the flight identity, gaps and heading
wrap. The expected variable definitions come from the campaign's example.
[Campaign file header](https://archive.eol.ucar.edu/raf/Projects/ICEBRIDGE/LRTdump.html)

The motion calculation reports the shortest rotation between each two valid
consecutive one-second attitude samples. That gives a lower bound on how fast
the reported orientation changed at some point in the interval. Faster changes
could cancel before the next report. Because the attitude comes from the
aircraft's inertial reference system, it serves as a separate motion check.
It has no role in the gyro-free model score or in an independent Earth-model
decision. [Motion-source audit](MOTION_SOURCE_AUDIT.md)

When the original is available, run from the repository root. The intake
supports classic and 64-bit-offset netCDF and writes a hash-bound local report.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- \
  ~/venv/bin/python -m lll.ilvis0_ncar_rf04 /path/to/RF04.nc \
  --output /path/to/rf04-motion-intake.json
```
