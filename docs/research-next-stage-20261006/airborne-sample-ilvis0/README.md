# First time-tagged airborne IMU sample

This ILVIS0 file contains a real airborne IMU stream over Greenland on 14 April 2009:
132,444 time-tagged IMU packets at approximately 200 Hz, spanning 662.226 seconds (about
11 minutes), together with navigation and primary GPS receiver data. All 143,471 outer
packet checksums pass. No unframed bytes or IMU timestamp gaps above 7.5 ms were found.

The instrument identifies AV-510 VER5, firmware04.60, ICD15.00 and IMU8. The public
[2014 interface document](https://asapdata.arc.nasa.gov/share/ASF_Applanix/POSv6_User_ICD.pdf)
matches observed outer packet layouts but describes the IMU payload as 24 bytes without
physical scaling and axis definitions. It is a later version than this instrument.
The payload is therefore preserved exactly. No physical gyro rates, angular increments
or Earth-model results have been produced.

Reassembling the primary GPS stream across packet boundaries recovers 660 checksum-valid
GGA position messages, 660 VTG motion messages and 660 ZDA date/time messages. All GGA
fix-quality values are 1. ZDA confirms the date. Under the compatible public header definition,
the first timestamp is UTC seconds of the week and the second is instrument time since
power-on. Receiver fix timing, IMU latency and lever arms still need verification.

The 662 fused navigation records describe a mainly southbound track from about 79.72°N to
78.86°N. Altitude rises from about 6.9 to 7.5 km, and roll reaches approximately −17.5°.
This segment includes a climb and maneuvers; it is not an already qualified level-cruise
window. Navigation-derived orientation/rates must not substitute for independent gyro data.

Preserved files:

- The original `.013` log, compressed without changing its uncompressed bytes.
- `imu-packets.csv.gz`: offsets, timestamps, status and exact opaque IMU payloads.
- `navigation.csv`: explicitly labeled fused position, velocity and orientation.
- `primary-gps-stream.bin.gz`: reassembled receiver stream.
- `gps-sentences.txt` and `gps-fixes.csv`: verified receiver sentences and position fixes.
- The inspection record with source/helper hashes, timing and unresolved assumptions.

Reproduce into a new output directory using the original downloaded file:

```sh
/home/sweisman/venv/bin/python analysis/tests/inspect_ilvis0_sample.py --input /home/sweisman/Downloads/ILVIS0_gyro_54935_atm_applanix_14Apr09.013 --output-dir /tmp/ilvis0-reinspection
```

The inspector fails on malformed outer framing/checksums and never repairs or interpolates.
Two focused checks pass: whole-frame checksum convention/truncation, and receiver sentence
reconstruction/checksum/signed coordinate conversion. No full suite, campaign or model fit ran.

Next obtain an instrument-specific IMU8 payload definition or an export preserving independent
physical angular increments/rates, units, axes, timing and known corrections. More log files
are unnecessary until that is resolved. A documentation-request draft is in the
[airborne inspection notes](../AIRBORNE_DATA.md); no message has been sent.

Data citation: Hofton, M. & Blair, J. B. (2011).
[IceBridge LVIS L0 Raw Ranges, Version 1](https://nsidc.org/data/ilvis0/versions/1).
NASA NSIDC DAAC. DOI10.5067/E6JPQ3QNW77R. Subset:
`ILVIS0_gyro_54935_atm_applanix_14Apr09.013`, inspected6October2026.
