# Predicting the later flight

**49/72 returned fits passed their numerical stopping checks.** The frozen definition contains 72 starts.

Each model calibrates on earlier receiver positions and IMU increments, then
predicts later positions from the continuous IMU stream without a GPS reset.
Later GPS positions only score the saved forecast. Height counts alongside
horizontal error. Start selection uses converged training cost alone.

These are retrospective development results. Accuracy screens are descriptive;
neither a small error nor a relative advantage establishes calibrated significance.

| Stretch | Source recording | IMU format code | GPS fixes |
|---|---|---:|---:|
| A | ILVIS0_applanix_55128_Ames_510-24Oct09_24Oct09.013 | 8 | 668 |
| B | ILVIS0_applanix_55277_20100322_610_AMES_08Dec09.013 | 21 | 436 |
| C | ILVIS0_applanix_55133_610-29Oct09_29Oct09.013 | 21 | 669 |

| Stretch | Candidate | Removal | Clock | Primary start | Later horizontal RMS, m | Later height RMS, m | Accuracy screen |
|---|---|---|---|---:|---:|---:|---|
| A | Globe, specified field | None | header_elapsed | — | Unavailable | Unavailable | No qualified primary |
| A | Globe, specified field | None | nominal_200Hz | 1 | 19.317 | 10.4847 | Failed |
| A | Globe, specified field | Profiled | header_elapsed | — | Unavailable | Unavailable | No qualified primary |
| A | Globe, specified field | Profiled | nominal_200Hz | 0 | 15.5264 | 10.5482 | Failed |
| A | Globe, zero field | None | header_elapsed | 0 | 1359.92 | 24.4062 | Failed |
| A | Globe, zero field | None | nominal_200Hz | 0 | 1360.25 | 24.39 | Failed |
| A | Globe, zero field | Profiled | header_elapsed | 0 | 1359.92 | 24.4062 | Failed |
| A | Globe, zero field | Profiled | nominal_200Hz | 0 | 1360.25 | 24.39 | Failed |
| A | Stationary disc | None | header_elapsed | 0 | 585.624 | 63.7363 | Failed |
| A | Stationary disc | None | nominal_200Hz | — | Unavailable | Unavailable | No qualified primary |
| A | Stationary disc | Profiled | header_elapsed | 0 | 585.625 | 63.7362 | Failed |
| A | Stationary disc | Profiled | nominal_200Hz | — | Unavailable | Unavailable | No qualified primary |
| B | Globe, specified field | None | header_elapsed | 1 | 1.12968 | 3.28609 | Passed |
| B | Globe, specified field | None | nominal_200Hz | 1 | 1.1309 | 3.2799 | Passed |
| B | Globe, specified field | Profiled | header_elapsed | 1 | 0.83814 | 3.26529 | Passed |
| B | Globe, specified field | Profiled | nominal_200Hz | 1 | 0.838794 | 3.25907 | Passed |
| B | Globe, zero field | None | header_elapsed | 0 | 496.283 | 7.23248 | Failed |
| B | Globe, zero field | None | nominal_200Hz | 1 | 496.284 | 7.24027 | Failed |
| B | Globe, zero field | Profiled | header_elapsed | 1 | 496.283 | 7.232 | Failed |
| B | Globe, zero field | Profiled | nominal_200Hz | 0 | 496.286 | 7.24032 | Failed |
| B | Stationary disc | None | header_elapsed | 0 | 793.417 | 35.7545 | Failed |
| B | Stationary disc | None | nominal_200Hz | 1 | 793.418 | 35.7613 | Failed |
| B | Stationary disc | Profiled | header_elapsed | 1 | 793.416 | 35.7535 | Failed |
| B | Stationary disc | Profiled | nominal_200Hz | 1 | 793.418 | 35.7613 | Failed |
| C | Globe, specified field | None | header_elapsed | 0 | 3.30147 | 8.91006 | Passed |
| C | Globe, specified field | None | nominal_200Hz | 1 | 3.30361 | 8.91085 | Passed |
| C | Globe, specified field | Profiled | header_elapsed | — | Unavailable | Unavailable | No qualified primary |
| C | Globe, specified field | Profiled | nominal_200Hz | 0 | 2.18387 | 8.54417 | Passed |
| C | Globe, zero field | None | header_elapsed | — | Unavailable | Unavailable | No qualified primary |
| C | Globe, zero field | None | nominal_200Hz | 1 | 32.3092 | 6.3281 | Failed |
| C | Globe, zero field | Profiled | header_elapsed | — | Unavailable | Unavailable | No qualified primary |
| C | Globe, zero field | Profiled | nominal_200Hz | — | Unavailable | Unavailable | No qualified primary |
| C | Stationary disc | None | header_elapsed | 1 | 312.591 | 7.91097 | Failed |
| C | Stationary disc | None | nominal_200Hz | 1 | 312.59 | 7.90872 | Failed |
| C | Stationary disc | Profiled | header_elapsed | 0 | 67.9016 | 5.1071 | Failed |
| C | Stationary disc | Profiled | nominal_200Hz | 0 | 67.9014 | 5.10951 | Failed |

The run charged 3,342 native calculations. Unfinished and failed starts remain in the sealed evidence, including alternatives
to each displayed primary. Differences between starts describe sensitivity,
not a confidence interval. A smaller horizontal error cannot excuse an
implausible height reconstruction.

[Selection and splits](../ilvis0-prediction-pilot-preparation/README.md) · [Scientific plan](PLAN.md) · [Packaging correction](../ilvis0-prediction-pilot-preparation/LOADER_REPAIR.md) · [Prediction protocol](../PREDICTION_VALIDATION.md)
