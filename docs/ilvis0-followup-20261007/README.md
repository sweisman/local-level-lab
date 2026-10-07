# Airborne timestamp, configuration and performance follow-up

The local follow-up is complete. It checked all 268 originals preserved after initial screening,
without downloading more files or changing the original screening ledger. The other 58 files
had already been rejected for lacking qualifying level-flight data.

| Follow-up result | Files |
| --- | ---: |
| Candidate level-flight windows | 80 |
| No qualifying window after timing was resolved | 35 |
| Still blocked by navigation alignment | 153 |

Timestamp checks passed in every file. GPS-time tags were converted using the documented time
basis and dated leap seconds, checked against embedded receiver dates/times and available
dual GPS/UTC headers. The geometry, maneuver and full-navigation requirements were preserved.
This recovered 62 candidate files. The 35 newly classified no-level owned originals were
subsequently removed under the standing discard instruction, after verifying their hashes and
writing durable disposition records. Together with the initial 58 rejections, 93 files have been
discarded. All 80 candidate files and 153 unresolved originals remain. The historical screening
ledger and reports are preserved; the follow-up cleanup journal records the later disposition.

Among the 153 remaining cases, 133 report fine alignment throughout, two report an earlier
alignment stage, and 18 mix full navigation with fine alignment. Those statuses do not establish
the orientation accuracy required by the current screen. One also has missing nearby GPS context.

## What the performance measurements show

There are 108 candidate windows totaling about 9.27 hours across instrument files. Simultaneous
recordings can overlap, so that total is not a count of independent flight hours. Window speeds
range from about **140 to 256 metres per second**. The corresponding predicted horizontal globe
transport rates range from **4.5 to 8.3 degrees per hour**. These are model predictions from
flight context, not measured evidence of Earth's shape.

Eleven exact observed instrument configurations were investigated. Two POS AV 510/IMU8
configurations reproduced the physical-channel checks on two dates each. Four candidate files
passed per-file physical checks, providing about **32.4 minutes** for observed gyro characterization.
IMU6 and IMU21 did not pass the IMU8 interpretation/scales; their converted observations remain
unaccepted. Several IMU21 cases have very high correlations with different fitted scales, and
one configuration also shows axis/sign differences. Separate empirical decoding is required.

In the four supported recordings, variation among one-minute body-axis gyro averages is about
**5.7–21.7 degrees per hour**, depending on recording and axis. This includes real aircraft
motion, vibration, sensor noise and processing. Some recordings supply only four or five full
minute blocks. These figures are descriptive and are not an estimate of intrinsic gyro accuracy
or a calibrated significance test. The decoded single-sample angular-rate quantization step is
about 157 degrees per hour at 200 Hz; it is not the precision of a long average.

Slower flight reduces the curvature-related signal, while aircraft motion and unknown bias need
not decrease with speed. Instrument quality alone therefore does not settle usability. Heading
coverage, orientation reconstruction, processing independence and averaging behavior matter.

No Earth-model fit, synthetic campaign or calibrated winner claim was made. The next work is
independent decoding of the other IMU configurations and resolving orientation/processing limits.
Fine-alignment records remain preserved without relaxing the scientific gate.

## Can recordings be joined into longer windows?

All 326 file spans were checked using embedded receiver dates, rather than filenames alone,
and grouped by the same observed instrument configuration. Four overlapping pairs were found.
Three are byte-identical duplicates and add no measurement time, including a pair cataloged
on different dates. Those copies must not count as independent observations.

The remaining pair, two 29 August 2017 recordings from the same POS AV 610, has 130,221 exactly
matching IMU packets in its overlap. Their navigation and GPS context also match. Combining
unique measurements extends coverage by about 16.7 seconds, but the combined recording still
has no qualifying one-minute level window. No qualifying stretch was lengthened in this archive.
The closest separated same-instrument recordings have an 18.5-minute gap, which cannot be
bridged. Different simultaneous IMUs are not concatenated into one continuous measurement.

`file-continuity.json` records these checks. The reusable checker verifies overlap or a continuous
sample boundary, rejects inconsistent measurements and gaps, and applies the original screen
to combined context. It does not interpolate, repair data, export a fabricated gyro series, or
modify original files. Four focused continuity tests pass.

## Reproducible evidence

`completion.json` contains aggregate results. `summary.json.gz` preserves the per-file timing,
alignment, window and predicted-signal reports. `physical-and-variability.json.gz` contains
configuration checks and observed gyro statistics. `manifest.json` and `source-freeze/` preserve
the implementation/environment freeze. Lossless originals remain in `data/ilvis0-ready/`;
the interruption-safe local output is `data/ilvis0-followup-20261007/`.

`cleanup-completion.json` records the later removal of 35 confirmed rejections. Their detailed
prepare/remove journal is `data/ilvis0-followup-20261007/cleanup.jsonl`. These changes reclaimed
about 199 MiB of compressed originals and do not affect the retained candidate/unresolved files.

Time conventions come from the [Applanix interface document](https://asapdata.arc.nasa.gov/share/ASF_Applanix/POSv6_User_ICD.pdf);
the dated corrections follow [NIST's leap-second history](https://www.nist.gov/pml/time-and-frequency-division/time-realization/leap-seconds).
