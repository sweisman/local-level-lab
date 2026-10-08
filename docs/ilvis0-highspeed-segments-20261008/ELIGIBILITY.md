# Which airborne recordings are used?

This selection contains 53 distinct stretches totaling 424.3 minutes. All 232 retained files were checked.

The [stretch catalog](eligible-stretches.csv) identifies the original file, its SHA-256 fingerprint, exact UTC start/end, duration, minimum/median receiver ground speed and instrument/mounting epoch. The [file ledger](files.csv) also includes files with no qualifying stretch or unresolved context. Byte-identical aliases are recorded and analyzed once. Different instruments on the same flight may overlap in time; these totals are not independent-flight counts.

A stretch must satisfy every rule below, selected before any Earth-model residual is examined:

- At least 240 continuous seconds after all exclusions and boundary guards.
- Every associated GPS receiver ground-speed observation is at least 700 km/h. Speed through the air and flight-average speed do not establish this condition.
- Fused motion context reports full alignment, roll within ±5°, vertical speed within ±1.5 m/s, and central course-change rate at most 0.05°/s. This samples steady flight; it does not establish that smaller aircraft corrections are absent.
- Motion and receiver gaps are at most 2 seconds. No interpolation or course smoothing fills them. Checksummed VTG speed requires a unique dated GGA association within 0.5 seconds; valid position quality and both altitude and geoid separation are required.
- Ten seconds are removed from each end of a qualifying motion/speed interval. An additional 0.2-second raw-data guard supports the ±0.15-second timing sensitivity.
- Raw IMU framing/checksums are valid, rate code is 2, status fields report no error, adjacent intervals are within 2.5–7.5 ms and time basis, IMU type and logged installation signature stay fixed. Gaps or configuration changes split stretches.
- Dated embedded receiver UTC agrees with the documented packet time basis. Unsupported framing, timing or context is recorded rather than repaired.

Fused navigation is used only for motion selection, never as an independent Earth-model observation. Geometry eligibility and supported physical conversion are separate: an eligible stretch can still be unsupported, fail numerical convergence, or contain insufficient model information. Four minutes and 700 km/h are development criteria, not a detection guarantee.

The complete selected stretch is the primary joint fit. Fixed 4–10-minute sections check its residual consistency with the same fitted parameters; they are not independent trials or separate calibration fits. Selection records and criteria are frozen before fitting. Changing the policy requires a separately versioned inventory. Original recordings are preserved.

Policy: `ilvis0-all-highspeed-level-segments-v1`. Technical selection SHA-256: `934dea342a64b716533732d7ab0e961d23709cf37499faf7cee8e4c386778809`.
