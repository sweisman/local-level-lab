# GPS-only reconstruction of six airborne recordings

The six prepared recordings now have positions reconstructed from their GPS receiver's
satellite measurements, separately from Applanix's combined GPS/IMU navigation answer.
All 2,968 previously selected position epochs were solved by both fixed methods: **5,936
primary solutions**, plus **24 checks from a displaced starting position**, all converged.
This advances the trajectory input needed for airborne IMU analysis. It does not yet
establish the trajectory's accuracy or produce a measured Earth-model result.

The first reported GPS position supplies only an initial numerical guess. Later reported
positions never constrain the reconstruction; they are used afterward for consistency
comparisons. No fused position, attitude, angular rate or uncertainty enters these solves.
No epochs were replaced or selected according to their residuals.

## What was computed

Both methods use recorded GPS ranges and broadcast satellite orbits, solving three position
coordinates and receiver clock offset at each epoch. They account for signal travel time,
satellite clock and relativistic corrections, and the conventional correction for Earth's
rotation during signal travel. These calculations assume conventional GPS/WGS84 geometry;
they are trajectory-development tools, not independent evidence comparing Earth's shapes.

The first method uses L1 code ranges and the ionospheric coefficients recorded in each file.
The second combines L1 and L2 ranges to remove the leading ionospheric term. Satellite group
delay is treated according to the combination used. Neither method solves carrier-phase
ambiguities or imports external signal-bias products. A standard atmospheric approximation
provides tropospheric delay, including the high-altitude portions of these recordings;
actual weather and humidity were not measured. Equal range weights and a five-degree
computed elevation mask are fixed before comparison. Explicit health, range, ephemeris and
rank checks are retained. Measurements are not removed merely for having large residuals.

## Results and their limits

The table reports root mean square **differences from the same receiver's reported
positions**, in metres, along north/east/up axes. Those reports are not external ground truth.

| Recording date and stream | Epochs | L1 north/east/up | Dual-frequency north/east/up |
|---|---:|---|---|
| 2009-04-14 LVIS | 489 | 0.366 / 0.172 / 1.062 | 1.974 / 0.716 / 2.849 |
| 2014-09-16 POS510 | 482 | 0.233 / 0.207 / 0.506 | 0.673 / 1.856 / 1.840 |
| 2010-10-26 LVIS | 486 | 0.231 / 0.289 / 0.455 | 0.705 / 0.751 / 2.148 |
| 2010-11-20 LVIS | 483 | 0.687 / 0.253 / 1.788 | 0.770 / 0.871 / 1.307 |
| 2015-09-24 LVISGH | 459 | 0.854 / 0.329 / 1.296 | 1.160 / 0.833 / 1.906 |
| 2017-09-20 B200T / 510i | 569 | 0.229 / 0.227 / 0.648 | 0.939 / 0.934 / 2.035 |

The displaced-start checks reproduce positions within 1.7e-8 metres. That establishes
numerical convergence for those checks, not positional accuracy. L1 agrees more closely
with the receiver reports, but shared data and similar processing can produce that agreement.
The dual-frequency combination amplifies code noise and can expose unmodeled signal biases;
its greater differences do not by themselves show which solution is more accurate.

Successive one-second differences are correlated: lag-one correlations across methods and
axes range from 0.20 to 0.89. Mean vertical differences between methods range from about
-1.61 to +2.97 metres. Treating each epoch as an independent, unbiased observation would
therefore be unsupported. Formal uncertainties derived from range residuals and satellite
geometry are preserved, but their coverage is **not calibrated**. Common orbit errors,
atmospheric errors, signal biases and temporal correlations remain unresolved.

## Reproducibility and next work

Implementation: [gnss_position.py](../../analysis/lll/gnss_position.py),
[ilvis0_position.py](../../analysis/lll/ilvis0_position.py), and
[worker](../../analysis/tests/ilvis0_position_worker.py). Twenty-eight focused tests pass:
13 new positioning/workflow tests and 15 preceding receiver-decoder tests. Checks cover
clock/atmosphere corrections, independently constructed known-position controls, displaced
seeds, rank failures, retained bad ranges, dual-frequency treatment and input/epoch guards.

The completed run is frozen in `data/ilvis0-position-20261007/`. Its manifest hashes source,
inputs and numerical environment; source snapshots, per-file receipts and atomic reports
preserve interruption recovery for unfinished work only. **Do not resume this completed run
or substitute revised code into it.** This directory preserves the compact reports,
manifest, completion and source snapshots. The [inventory](inventory.csv) records exact
filenames, source hashes and per-method statistics. Larger per-epoch CSV/JSONL exports stay
in the data directory. [export_inventory.py](export_inventory.py) verifies the frozen evidence
and rebuilds this compact handoff without rerunning positioning.

All 232 stored originals remain. There were zero downloads, deletions, Earth-model fit
attempts, scientific eligibility changes or synthetic campaigns in this step.

Next, develop conservative trajectory-error sensitivity checks that retain temporal
correlation and systematic offsets, rather than accepting these formal uncertainties as
validated covariance. IMU6 processing, calibration, mounting and integration/latency bounds
also need support before observed Earth-model fitting. These IMU6 streams must not inherit
the performance specifications of the different IMU8 reference. The existing bounded
Earth-fit allowance remains unused.

Structural and numerical references:
[Trimble ionosphere/UTC packet](https://receiverhelp.trimble.com/oem-gnss/icd-pkt-response55h-utc-ion.html),
[GPS interface specification](https://www.navcen.uscg.gov/sites/default/files/pdf/gps/IS-GPS-200N.pdf),
[RTKLIB code positioning](https://raw.githubusercontent.com/tomojitakasu/RTKLIB/master/src/pntpos.c),
[broadcast ephemeris implementation](https://raw.githubusercontent.com/tomojitakasu/RTKLIB/master/src/ephemeris.c),
[atmosphere and range corrections](https://raw.githubusercontent.com/tomojitakasu/RTKLIB/master/src/rtkcmn.c),
and [NASA standard atmosphere](https://www.grc.nasa.gov/www/k-12/airplane/atmosmet.html).
