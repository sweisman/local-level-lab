# IMU21 units and unresolved-flight assessment

This separate local assessment has completed checks of the 233 originals preserved after screening.
It leaves earlier evidence and all remaining originals intact. No new recordings are downloaded
and no Earth-model tests are run.

The proposed IMU21 angle scale is **2⁻²⁸ radians per count**. The proposed velocity increment
scale is **2⁻²¹ feet per second per count**, converted with exactly 0.3048 metres per foot.
These are fixed empirical hypotheses. A manufacturer scale table has not been found.

## Results

| Check | Result |
| --- | ---: |
| Preserved sources checked without context errors | 233 |
| IMU21 files individually tested | 98 |
| Files passing physical checks | 71 |
| Configurations reproducing on both selected dates | 3 of 6 |
| Candidate files exported after both configuration and file checks | 24 |
| Exported qualifying time across instrument streams | 167.8 minutes |
| Unresolved files with GPS-only potential stretches | 84 of 153 |

Together with the earlier four IMU8 candidates, 28 candidate files now have supported physical
units and about 200 minutes of qualifying data. Simultaneous instrument streams can overlap;
these minutes are not necessarily independent flight time. Decoded units do not resolve
processing independence or orientation, so no Earth-model fit has run.

The successful two-date configurations are POS AV 610 serials 3861, 3894 and 6448, each at
200 Hz with IMU21. Serial 3894 consistently reverses Y and Z relative to the Group-1 reference;
its exported measurements retain their native axes. Serials 3456, 5680 and 7763 each failed
one of their two preselected dates. Their individually passing files are recorded, but the
configuration gate prevents exporting them as accepted physical candidates. No failed date
was replaced after looking at its gyro results. In total, 27 files failed an engineering or
chronological stability check; those failures remain available for investigation.

All 153 alignment-blocked files remain unresolved scientifically. GPS-only screening found
potential stretches in 84 of them, totaling about 7.14 hours across potentially overlapping
streams. That result identifies where further orientation work may be worthwhile; it does
not establish level attitude or authorize discarding the other 69 files.

For each exact instrument configuration, two files are chosen using existing geometry, actual
receiver dates and distinct source hashes. The first determines a candidate axis/sign mapping;
the second must reproduce it. Gyroscope and accelerometer checks share that mapping and
retain the existing correlation, scale-error and chronological stability limits. Every retained
IMU21 file is subsequently checked individually. Physical window exports require both the
two-date configuration check and that file's check. Raw integer increments and native axes
remain intact; validation offsets are never removed from exported measurements.

The first prototype closely matches both proposed scales, but one gyro axis fails the scale
stability requirement between recording halves. This is a recorded failure, not grounds to
relax the requirement or choose another reference file after seeing its result.

Navigation uncertainty is examined separately. The archive's older 76-byte Group-2 packets
have a plausible nine-float uncertainty prefix; that interpretation is marked **inferred**.
The 88-byte layout is described in the [Applanix interface document](https://asapdata.arc.nasa.gov/share/ASF_Applanix/POSv6_User_ICD.pdf).
Raw payloads are preserved. The reported values are internal estimates from the fused
navigation solution, not independently demonstrated orientation accuracy.
The audit encountered 102,926 legacy packets and 18,253 documented V6 packets. For example,
the 14 April 2009 LVIS recording remains in fine alignment while the inferred legacy fields
report median roll/pitch uncertainty about 0.019 degrees and heading uncertainty about
0.397 degrees. Thus the broad alignment flag alone does not describe its reported precision;
neither the inferred layout nor the internal estimate independently verifies that precision.

The GPS-only screen uses checksummed position and height reports, with 31-second height
regressions and 11-second velocity/course regressions. It requires complete nearby samples,
applies speed/climb/course limits and buffers window ends. These potential stretches do not
establish aircraft roll, IMU mounting, alignment or brief maneuvers. They neither promote a
scientific candidate nor authorize discarding an unresolved source.

The completed worker wrote a new source/environment/input manifest, per-file reports,
uncertainty CSVs and any accepted physical-window CSVs in
`data/ilvis0-imu21-assessment-20261007/`. It rejects changed inputs and source revisions.
The worker has released its process lock. Do not resume this completed assessment or rewrite
its source/input freeze. Focused verification passed 25 tests. `completion.json` preserves
aggregate counts and the configuration decisions; `summary.json.gz` preserves all final
diagnostics and per-file physical checks. The manifest and `source-freeze/` preserve the
implementation. All 233 originals remain; no files were deleted and no eligibility gate changed.
