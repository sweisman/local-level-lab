# Additional inertial-data sources

Two archives offer raw observations for separate development cohorts. Neither has
been added to the existing 53-stretch comparison. No new Earth-model fits have
been run on these sources.

**ESA confirmation is reserved before fitting.** Recording 187 is development
material. The other eight cataloged files form seven protected confirmation
groups. Integrity and receiver-only eligibility checks may proceed; model fitting
and outcome inspection wait for a frozen method and confirmation selection.
See the [provenance ledger and reservation](../analysis-provenance/README.md).

An **IMU (inertial measurement unit)** records angular motion and acceleration.
The relevant files contain its observations, rather than only a finished
navigation solution.

| Source | What is verified | What remains |
|---|---|---|
| ESA/DTU AirQuantumGrav and Green Quantum | The live catalog contains **nine raw iMAR files totaling 8.02 GB**. One complete recording has **9,168,819 records over 8.49 hours**, approximately **300 Hz**, with no gaps above 1.5 nominal periods. Its matching GNSS PPP position file is downloaded. | The [first frozen selection](../esa-development-selection/README.md) admits no intervals from recording 187. The [motion diagnostic](../esa-motion-diagnostic/INTERPRETATION.md) confirms noise sensitivity, but receiver-error assessment is still needed before another policy. The other eight raw recordings have not been downloaded or model-tested. |
| Wuhan University SmartPNT-POS | The public catalog contains **652 files**, including **40 IMR files**. One downloaded airborne sample contains **115,696 IMU records over 19.28 minutes**, with no timestamp reversal, duplicate or gap exceeding 1.5 nominal sample periods. | Independent receiver positions, dataset-specific motion screening and model qualification remain to be developed. |
| SmartPNT-POS long-record lead | Header and endpoint range requests verify a **20.85-hour timestamp span** for a 600 Hz HG4930 file in the Allan-variance folder. Only **576 bytes** were downloaded. | Interior completeness, stationary conditions and mounting are unverified. It is a sensor-characterization lead, not curvature evidence. |

## Longer, slower airborne surveys

The [ESA report](https://earth.esa.int/eogateway/documents/d/earth-online/airquantumgrav-final-report)
lists survey-leg speeds around 120–130 knots, or 222–241 km/h. Longer duration can
compensate for slower travel in accumulated surface curvature: 240 km/h for
30 minutes covers about the same distance as 700 km/h for ten minutes. It does
not automatically compensate for sensor bias or drift.

The [rate/body qualification](../esa-rate-qualification/INTERPRETATION.md) now
passes 48 generated controls while keeping constructed increments and unresolved
sampling/processing assumptions explicit.
The iMAR Level-0 files are documented as ASCII records of GPS time, three
accelerations, three angular rates in radians/second, and temperature. The report
states that their axes have already been rotated to aircraft forward, starboard
and down. It also describes separate raw GNSS observations in RINEX format.
The inspected recording confirms approximately 300 Hz cadence. Header units and
the report agree; the inspection does not independently calibrate the instrument.

The inventory distinguishes **nine files from twelve flight labels**: some flights
share a file. The 50 reported line intervals total 20.52 hours; that is observing
time, not fifty independent flights.

- [Reported IMU files](esa-reported-imu-files.csv)
- [Verified live IMU file catalog](esa-live-imu-files.csv)
- [Reported line intervals](esa-reported-lines.csv)
- [ESA catalog and access instructions](https://earth.esa.int/eogateway/campaigns/airborne-quantum-gravimetry-airquantumgrav-2023)
- [Dataset access request](https://esatellus.service-now.com/csp?id=dar_fast&dataset=AirQuantumGrav2023V0)

## Downloaded ESA recording

`187_rqh01.txt` covers **8.49 hours** on July 6, 2023. A streaming pass checked
every row, preserved the original and reproduced its acquisition hash. Timestamp
steps range from approximately 3.333 to 3.334 milliseconds. One startup row has
near-zero acceleration and is recorded as a quality flag; it has not been silently
removed. Eleven deterministic decoder tests check units, signed values, malformed
records, nonfinite values, timestamp ordering and gap handling.

The matching GNSS position export contains **64,080 epochs over 8.90 hours**.
The survey report identifies it as GNSS-only precise point positioning, using
satellite orbit and clock products. The export uses the software's generic
“GNSS/INS Epochs” label; the report, rather than that label, establishes the stated
processing provenance. Raw RINEX observations are available but have not been
independently reprocessed here.

Both reported lines for this recording overlap the IMU and GNSS time coverage:

| Reported line | Duration | Mean ground speed | Ellipsoid-height range |
|---|---:|---:|---:|
| 9001 | 6.13 minutes | 282 km/h | 1,949–1,952 m |
| 3007 | 57.4 minutes | 263 km/h | 1,512–1,902 m |

The longer line changes altitude substantially. These are descriptive survey
intervals, not approved steady-flight analysis windows. Admission will use the
independent trajectory and a published policy before any model-fit residuals are
examined. No Earth-model fits have been run on ESA data.

[IMU inspection](esa-sample-report.json) · [GNSS inspection](esa-gnss-report.json) ·
[Reported-line trajectory details](esa-selected-line-context.csv).

## Downloaded Wuhan sample

The [SmartPNT-POS archive](https://www.kaggle.com/datasets/fengzhusgg/smartpnt-pos)
includes fourteen UAV datasets among thirty numbered collections. The inspected
sample is `Data06_20210115_HG4930_UAV_Opensky`. Its IMR header identifies a
**NovAtel SPAN HG4930**, 100 Hz angle/velocity increments, GPS time tags and
explicit conversion scales. Its mounting XML supplies a 90° rotation and antenna
lever arm. The binary original and signed integer counts are preserved.

The matching **raw RINEX 3.02 GNSS file** contains 5,796 observation epochs over
19.32 minutes. Receiver positions have not been computed. A separately downloaded
reference trajectory is explicitly labeled **smoothed, combined GNSS/INS**. Its
reported maximum speed is only **29.2 km/h**; this is motion context, not independent
position evidence or a basis for admission.

The streaming inspector follows the
[manufacturer’s IMR specification](https://docs.novatel.com/Waypoint/Content/Data_Formats/IMR_File.htm),
honors increment-versus-rate flags, preserves original time tags and applies no
mounting, timing-bias or Earth-rate correction. Twelve deterministic format tests
pass. IMR has no record checksum; structural checks and file hashes do not prove
which corrections preceded conversion into IMR.

[Complete file inventory](smartpnt-files.csv) ·
[Airborne sample inspection](smartpnt-sample-report.json) ·
[Long-record range inspection](smartpnt-long-record-report.json).

## Admission to future analyses

Each dataset will have its **own published eligibility policy**, fixed before
examining model-fit residuals. Source integrity, timing continuity, independent
receiver trajectory, usable duration, traveled distance and aircraft motion will
determine candidate intervals. Instrument performance assumptions and processing
hypotheses must also be qualified separately.
The [ESA selection proposal](ELIGIBILITY_PLAN.md) specifies the intended longer,
slower cohort and required software controls. It has not yet selected intervals
or admitted them to model fitting.

Longer, slower survey lines can form a separate shape-analysis cohort. Short,
slow UAV tracks and stationary recordings may instead support noise, drift,
timing or rotation-field development. Raw availability alone admits no recording
to a shape conclusion. Existing intervals, results and thresholds stay unchanged.

Downloaded originals, reference documents, metadata pages and physical-unit CSV
are retained locally under `data/external-imu-survey-20261018/`. The
`build_inventory.py` command regenerates inspection reports from those explicit
inputs without network access, numerical integration or model fitting; hashes
are recorded in `inventory-receipt.json`.

The ESA additions have separate acquisition and inspection receipts under
`esa-sample/`. `inventory_esa.py` rebuilds the live catalog from saved directory
listings; `inspect_esa_gnss.py` describes the GNSS export and reported lines.
`inspect_esa.py` preserves its completed full-file inspection and refuses an
accidental repeat. It performs no model fitting. The initial bounded byte-range
request timed out on transfer closure and remains an incomplete diagnostic
fragment; all reported full-file checks use the independently completed original.

[Next analyses](../NEXT_STEPS.md) · [Study index](../STUDIES.md).
