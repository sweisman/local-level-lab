# Every start in the matched comparison

Completed **38 starts /2376 native calls /6.59 hours**. All eight preflight checks passed. Fresh controls passed.

[Complete attempt metadata and calibration CSV](attempts.csv). Biases are in rad/s for gyroscopes and m/s² for accelerometers; gains are dimensionless. Height errors are unscored. Receiver coordinates still use conventional geodetic construction.

| Case | Model | Seed | Initial time (ms) | Final time (ms) | Last cost | Numerical stop | Selected? | Unscored height RMS (m) |
|---|---|---|---:|---:|---:|---|---|---:|
| bias1_unsubtracted | sphere_rotating | primary | -120 | 27.547285 | 0.080797796 | pass |  | 648.22208 |
| bias1_unsubtracted | sphere_rotating | primary | 0 | 27.546938 | 0.080797796 | pass |  | 648.22216 |
| bias1_unsubtracted | sphere_rotating | primary | 120 | 34.734896 | 0.08071495 | pass | yes | 645.93525 |
| bias1_unsubtracted | sphere_rotating | repeat | -120 | 27.547332 | 0.080797796 | pass |  | 648.22206 |
| bias1_unsubtracted | sphere_rotating | repeat | 0 | 27.546936 | 0.080797796 | pass |  | 648.22216 |
| bias1_unsubtracted | sphere_rotating | repeat | 120 | 34.735917 | 0.08071495 | pass | yes | 645.93515 |
| bias1_unsubtracted | sphere_still | primary | -120 | -84.228165 | 5.5641762 | pass |  | 24773.526 |
| bias1_unsubtracted | sphere_still | primary | 0 | -68.478113 | 5.5633678 | pass | yes | 24777.529 |
| bias1_unsubtracted | sphere_still | primary | 120 | -29.505195 | 5.5713088 | pass |  | 24787.456 |
| bias1_unsubtracted | sphere_still | repeat | -120 | -84.228463 | 5.5641762 | pass | yes | 24773.526 |
| bias1_unsubtracted | sphere_still | repeat | 0 | -103.18655 | 5.5730736 | pass |  | 24768.744 |
| bias1_unsubtracted | sphere_still | repeat | 120 | -103.1867 | 5.5730736 | pass |  | 24768.743 |
| bias1_unsubtracted | flat_still | primary | -120 | -150 | 3645.6083 | pass |  | 19646.342 |
| bias1_unsubtracted | flat_still | primary | 0 | -150 | 3645.6083 | pass |  | 19646.342 |
| bias1_unsubtracted | flat_still | primary | 120 | -150 | 3645.6083 | pass | yes | 19646.342 |
| bias1_unsubtracted | flat_still | repeat | -120 | -150 | 3645.6083 | pass |  | 20299.488 |
| bias1_unsubtracted | flat_still | repeat | 0 | -150 | 3645.6083 | pass | yes | 20299.488 |
| bias1_unsubtracted | flat_still | repeat | 120 | -150 | 3645.6083 | pass |  | 20299.488 |
| bias1_profiled_removal | sphere_rotating | primary | -120 | 27.547285 | 0.080797796 | pass |  | 648.22208 |
| bias1_profiled_removal | sphere_rotating | primary | 0 | 27.546938 | 0.080797797 | pass |  | 648.22216 |
| bias1_profiled_removal | sphere_rotating | primary | 120 | 34.736523 | 0.080714951 | pass | yes | 645.93509 |
| bias1_profiled_removal | sphere_rotating | repeat | -120 | 27.547332 | 0.080797796 | pass |  | 648.22207 |
| bias1_profiled_removal | sphere_rotating | repeat | 0 | 27.546935 | 0.080797797 | pass |  | 648.22216 |
| bias1_profiled_removal | sphere_rotating | repeat | 120 | 34.735917 | 0.08071495 | pass | yes | 645.93515 |
| bias1_profiled_removal | sphere_still | primary | -120 | -84.228463 | 5.5641762 | pass |  | 24773.526 |
| bias1_profiled_removal | sphere_still | primary | 0 | -68.478113 | 5.5633678 | pass | yes | 24777.529 |
| bias1_profiled_removal | sphere_still | primary | 120 | -29.505195 | 5.5713088 | pass |  | 24787.456 |
| bias1_profiled_removal | sphere_still | repeat | -120 | -84.228463 | 5.5641762 | pass | yes | 24773.526 |
| bias1_profiled_removal | sphere_still | repeat | 0 | -103.18655 | 5.5730736 | pass |  | 24768.744 |
| bias1_profiled_removal | sphere_still | repeat | 120 | -103.1867 | 5.5730736 | pass |  | 24768.743 |
| bias1_profiled_removal | flat_still | primary | -120 | -150 | 1774.1119 | pass |  | 19682.31 |
| bias1_profiled_removal | flat_still | primary | 0 | -139.93681 | 1774.0759 | unresolved |  | 19684.343 |
| bias1_profiled_removal | flat_still | primary | 120 | 150 | 1774.0691 | pass | yes | 19742.795 |
| bias1_profiled_removal | flat_still | repeat | -120 | -150 | 1774.1119 | pass | yes | 20335.779 |
| bias1_profiled_removal | flat_still | repeat | 0 | -150 | 1774.1119 | pass |  | 20335.779 |
| bias1_profiled_removal | flat_still | repeat | 120 | -150 | 1774.1119 | pass |  | 20335.779 |
| bias1_unsubtracted | sphere_rotating | primary | -59.446817 | -59.446817 | 5.2195721 | pass | control | 20467.948 |
| bias1_unsubtracted | sphere_rotating | repeat | -59.446784 | -59.446784 | 5.2195721 | pass | control | 20467.957 |

Selected means lowest returned cost within a fixed three-start family. An unfinished lowest-cost attempt remains unresolved; it is not replaced with a higher-cost successful start. Fit convergence, independent repeat agreement and fresh-control results are separate requirements.

[Matched dispositions and repeat checks](README.md) · [Frozen method](PLAN.md) · [Earlier two-recording result](../ilvis0-horizontal-repeat-audit-20261019/INTERPRETATION.md).
