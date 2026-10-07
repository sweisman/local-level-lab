# What the IMU6 recordings now establish

A [subsequent installation and clock investigation](../ilvis0-installation-clock-20261007/README.md)
explains the changed mapping with logged angle settings and strongly links the acceleration
failures to timestamp-based rate conversion. All six acceleration checks pass under an explicit
fixed 200 Hz period hypothesis; one gyro holdout still fails narrowly. The original results
below remain the record of the first cross-date check, and no automatic conversion is enabled.

The six-file check is complete. Three hardware/firmware configurations were represented by
their earliest and latest distinct embedded dates. Selection used existing metadata, not
gyro fit quality. Source hashes, packet checksums and dated GPS timing passed in all six.
These are professional POS AV 510 recordings, but IMU6 is a different type from the reference
IMU8. Its exact sensor identity and performance cannot be inherited from the IMU8 description.

The gyro increments support **0.4 arcsecond per count**, or π/(180 × 9000) radians per count.
Five files pass with the axis mapping fixed from the earlier date. Two of the three
configurations therefore reproduce on both dates. This is an empirical result against
fused navigation channels; no authoritative manufacturer scale table was found.

| POS AV 510 serial | Dates checked | Mapping to the navigation reference | Frozen cross-date gyro check |
|---|---|---|---|
| 2720 | 14 April 2009; 16 September 2014 | X = −raw Y, Y = raw X, Z = raw Z | Pass |
| 3861 | 26 October; 20 November 2010 | X = −raw Y, Y = raw X, Z = raw Z | Pass |
| 4126 | 24 September 2015; 20 September 2017 | Earlier: X = raw Y, Y = −raw X, Z = raw Z | Fail on the later date |

The 2017 recording instead matches X = raw Y, Y = −raw Z, Z = −raw X. A separate diagnostic
learned each file's mapping on its first chronological half and tested it on its second half:
all six gyro checks passed. That explains the failed frozen-mapping comparison without
replacing it or declaring the configuration safe for automatic decoding. The same hardware
and firmware can report a different relationship to the navigation reference. Installation
settings, mounting and frame definitions need investigation; the fits alone do not prove
which mechanism changed.

The accelerometer interpretation remains incomplete. Horizontal channels suggest a velocity
increment scale near **3.38 × 10⁻⁵ metres/second per count**, but no exact scale is established.
Free fits account for orientation and a shared gravity magnitude; a scale estimated on the
first date is then held fixed on the second. **None of the six passes the complete three-axis
accelerometer requirements.** The vertical channel is less consistent, and scale/gravity
separation is sensitive to limited motion. These failures are preserved rather than relaxed.
No complete IMU6 physical decoder or acceleration export is enabled by this study.

Group 1 combines IMU and GPS information. It is useful for checking units and relative axes,
but is not independent evidence of Earth's shape or rotation. Constant offsets fitted in
these comparisons may include processing differences; they do not establish gyro bias or
show whether Earth rotation remains in Group 4. Sensor identity, onboard corrections,
absolute mounting orientation and latency/lever arms remain unresolved.

The reusable diagnostic is `analysis/lll/ilvis0_imu6.py`. Its worker finished and released
its lock. Durable results and compressed matched samples are in
`data/ilvis0-imu6-cross-date-20261007/`; this evidence directory preserves the source freeze,
manifest, complete report, axis-change supplement and CSV inventory. The original failed
cross-date result remains unchanged. No older audit was rerun, no original was deleted, and
no scientific window was promoted.
Twenty-three focused tests passed across the new diagnostics and existing decoder/motion
checks, including frozen mappings/scales, chronological instability and corrupt resume artifacts.
The supplementary calculation can be reproduced from the repository root with
`env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 /home/sweisman/venv/bin/python docs/ilvis0-imu6-cross-date-20261007/axis_change_supplement.py`.

Next: inspect recorded installation settings and investigate the vertical acceleration
discrepancy before extending a physical decoder to the remaining files. The
[course-filter controls](../ilvis0-course-controls-20261007/README.md) separately address
the proposed motion-screening timescale.
