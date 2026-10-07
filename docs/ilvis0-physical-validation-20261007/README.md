# Physical decoding of the Applanix reference

The 14 April 2009 ATM `.013` sample supports six signed, little-endian 32-bit increments:
velocity X/Y/Z followed by angle X/Y/Z. Independent numerical fits support the expected
scales, axis order and signs. This establishes an empirical decoder for the tested
AV-510 VER5, firmware04.60, ICD15.00, IMU8, rate-code2 configuration. It does not establish
every onboard correction or an independent Earth-model measurement.

The historical [sample corpus](../research-next-stage-20261006/airborne-sample-ilvis0/README.md)
remains unchanged apart from its living explanatory notes. Its original inspector treated
the 24-byte payload as opaque. The new streaming parser reproduces 143,471 valid outer
frames, 132,444 IMU packets, 662 fused navigation records, 5,934 primary receiver packets,
and 660 checksum-valid sentences of each GGA, VTG and ZDA type. No resynchronization,
checksum repair or science interpolation is used. Source SHA-256:
`18c48772bcd7e83566f2301ae3689d691c1675dfc2e60c0650b6e0017b764096`.

## Independent scale and axis checks

All 662 navigation timestamps match an IMU timestamp exactly. Rates use the actual adjacent
IMU interval. Group-1 gyro rates are converted from degrees/second to radians/second.
Each gyro scale and intercept is fitted freely before comparison with `2^-18 rad/count`.
Accelerometer validation fits three scales and offsets with **one shared gravity magnitude**,
using roll/pitch to express gravity in the aircraft frame. Comparing specific force directly
with translational acceleration would be physically wrong. The fitted shared gravity is
about 9.80553 m/s². It is a decoder cross-check, not a gravity or Earth-shape measurement.

| Channel | Fitted / expected scale | Correlation | RMS fitted residual |
| --- | ---: | ---: | ---: |
| Gyro X | 0.99998455 | 0.999999991 | 1.94 × 10⁻⁶ rad/s |
| Gyro Y | 0.99989011 | 0.999999570 | 3.58 × 10⁻⁶ rad/s |
| Gyro Z | 0.99976063 | 0.999999978 | 7.93 × 10⁻⁷ rad/s |
| Accelerometer X | 1.00016490 | 0.999999522 | 0.000248 m/s² |
| Accelerometer Y | 1.00007244 | 0.999999938 | 0.000338 m/s² |
| Accelerometer Z | 0.99999918 | 0.999997792 | 0.001426 m/s² |

The engineering criteria were correlation at least 0.9999 and scale agreement within 0.1%,
also required in both chronological half-record fits. These are conservative interpretation
checks, not statistical confidence bounds or manufacturer accuracy specifications. All
48 axis/sign mappings are tested with positive, physically plausible scales; allowing
negative fitted scales would make a sign check meaningless. The expected identity mapping
wins. Full reports retain intercepts, maximum and 99th-percentile residuals, fixed-binary-scale
residuals, alternative mapping scores and chronological holdout results.

The timing sensitivity report also compares preceding navigation-interval averages with the
endpoint fused reference. That is a diagnostic of averaging during maneuvers, rather than
an alternative acceptance rule or an interpolated scientific observation.

Gyro reference offsets are nonzero: approximately 1.60, 6.12 and 14.75 degrees/hour. Their
origin could involve frame conventions, navigation corrections, calibration, transport or
timing. Agreement does **not** prove that either stream includes or removes Earth's rotation.
These offsets are never subtracted from the exported IMU observations.

## Evidence and remaining uncertainties

The [public Applanix ICD](https://asapdata.arc.nasa.gov/share/ASF_Applanix/POSv6_User_ICD.pdf)
describes Group-1 aircraft-frame dynamics and its user-entered lever-arm reference. Its
Group-4 table gives the outer layout and 24 payload bytes, rather than the physical scale
table for this older instrument. No proprietary manufacturer scale table has been found.

| Topic | Status |
| --- | --- |
| Outer framing, lengths and checksum | Reproduced directly from bytes |
| Six signed integer fields and binary scales | Empirically supported for the reference configuration |
| Axis order and signs relative to Group 1 | Empirically supported |
| Increment convention and time-tag interval | Supported by reference agreement and observed cadence |
| Sensor calibration, scale/bias correction | Unknown; reference offsets are observable |
| Earth-rate compensation/subtraction | Unknown; a blocker for independent Earth inference |
| Coning, sculling, filtering, automatic zeroing | Unknown |
| Group-1 lever-arm reference | Documented structurally; actual configuration unavailable |
| Group-4 lever arms, exact mounting, physical latency | Unknown |

The geometry-only acquisition screen finds no qualifying one-minute level-flight window in
the reference. Its newly generated bulk products were discarded after recording that result;
the user's source and historical corpus were preserved. This folder keeps compact reports,
662 matched validation samples and the first 1,000 raw/physical IMU rows as decoder regression
evidence, selected by timestamp order rather than Earth-model fit quality.

The catalog tracks all 326 `.013` URLs and rounded metadata sizes. The six-file compatibility
trial completed using a user-authorized session credential held only in process memory.

| File/configuration | Physical decoding | Geometry disposition |
| --- | --- | --- |
| 14 April 2009 ATM, AV510/IMU8 | Empirically supported | No qualifying one-minute window |
| 16 April 2009 ATM, AV510/IMU8 | Independently supported on a second date | Keep: 272 seconds |
| 28 October 2010 AV510/IMU6 | Unresolved | Keep: fine-alignment navigation status |
| 10 May 2012 AV510/IMU6 | Unresolved | Keep: fine-alignment navigation status |
| 29 October 2015 AV610/IMU21 | Unresolved | Keep: 354 seconds |
| 20 September 2017 AV610/IMU21 | Unresolved | Keep: GPS time basis needs explicit UTC mapping |

This supports broader acquisition and screening, rather than applying IMU8 scales to every
sensor. Full-catalog screening has completed with two numerical threads and per-file
checkpoints: **18 retained, 58 confirmed no-level rejections, 250 unresolved**. Retained files
contain 22 windows totaling 7329.62 seconds across instrument streams; these are not necessarily
independent flights. Two retained ATM files have supported physical decoding and 692.01 seconds
of qualifying geometry. All unresolved originals remain preserved. The [completion report](corpus-screening.json)
records final counts and provenance hashes. No model fit,
simulation campaign, bootstrap, calibration or production promotion has run for ILVIS0.

See the [acquisition guide](../ILVIS0.md) for commands, retention policy and recovery.

The 250 unresolved files divide into 114 with GPS-time-tagged IMU logs, requiring an explicitly
validated mapping to receiver UTC, and 136 with UTC tags but insufficient valid navigation/GPS
context. Sixteen of the latter have some valid context. The next engineering work is timing
support and a navigation-status/context audit, followed by independent physical checks for each
IMU configuration. Originals are preserved. The [diagnosis](unresolved-diagnosis.json) records
the per-file grouping without changing the completed screen or eligibility rules.
