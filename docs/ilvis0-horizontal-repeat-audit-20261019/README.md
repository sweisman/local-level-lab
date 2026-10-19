# What horizontal-only refitting established

All twelve reconstructions and all 24 individual fits passed. The IMU8 stretch passes all six repeat checks and favors globe under both processing cases. The IMU21 stretch passes three of six repeat checks and remains unresolved in this sensitivity study; its primary and repeat costs both favor globe. The original 53-stretch findings remain unchanged.

| IMU | Processing case | Model | Horizontal RMS (m) | Unscored height RMS (m) | Objective |
|---:|---|---|---:|---:|---:|
| 8 | bias1_unsubtracted | sphere_rotating | 0.3741 | 2.047e+04 | 5.21957 |
| 8 | bias1_unsubtracted | sphere_still | 7.612 | 1.257e+04 | 1532.18 |
| 8 | bias1_unsubtracted | flat_still | 33.78 | 1.104e+05 | 16881.2 |
| 8 | bias1_profiled_removal | sphere_rotating | 0.3671 | 2.498e+04 | 5.11189 |
| 8 | bias1_profiled_removal | sphere_still | 7.612 | 1.257e+04 | 1532.18 |
| 8 | bias1_profiled_removal | flat_still | 17.46 | 1.104e+05 | 6777.58 |
| 21 | bias1_unsubtracted | sphere_rotating | 0.01425 | 648.2 | 0.0807978 |
| 21 | bias1_unsubtracted | sphere_still | 0.3009 | 2.477e+04 | 5.56418 |
| 21 | bias1_unsubtracted | flat_still | 16.82 | 1.965e+04 | 3645.61 |
| 21 | bias1_profiled_removal | sphere_rotating | 0.01425 | 648.2 | 0.0807978 |
| 21 | bias1_profiled_removal | sphere_still | 0.3009 | 2.477e+04 | 5.56418 |
| 21 | bias1_profiled_removal | flat_still | 9.013 | 1.968e+04 | 1774.11 |

The large unscored height errors are an important consequence of removing the vertical constraint. These solutions do not reconstruct plausible full three-dimensional flight paths. The successful IMU8 comparison shows that the score advantage persists without scoring height; it does not establish altitude or datum independence, isolate the gyroscope, or calibrate statistical significance.

| Stretch | Case | Model | Repeat passed | Timing difference (ms) | Relative cost difference |
|---|---|---|---|---:|---:|
| b365bdf39150ee6afc303ac1 | bias1_unsubtracted | sphere_rotating | True | 3.24973e-05 | 3.26781e-10 |
| b365bdf39150ee6afc303ac1 | bias1_unsubtracted | sphere_still | True | 0 | 4.57425e-12 |
| b365bdf39150ee6afc303ac1 | bias1_unsubtracted | flat_still | True | 0 | 2.70588e-12 |
| b365bdf39150ee6afc303ac1 | bias1_profiled_removal | sphere_rotating | True | -1.21767e-08 | 2.39833e-10 |
| b365bdf39150ee6afc303ac1 | bias1_profiled_removal | sphere_still | True | 0 | 2.87448e-11 |
| b365bdf39150ee6afc303ac1 | bias1_profiled_removal | flat_still | True | 0 | 1.14908e-12 |
| 7df21c836bec5751f83c0cce | bias1_unsubtracted | sphere_rotating | True | -5.04531e-05 | 1.6966e-10 |
| 7df21c836bec5751f83c0cce | bias1_unsubtracted | sphere_still | False | -18.9589 | 0.00159649 |
| 7df21c836bec5751f83c0cce | bias1_unsubtracted | flat_still | False | 0 | 1.62327e-09 |
| 7df21c836bec5751f83c0cce | bias1_profiled_removal | sphere_rotating | True | -2.50803e-06 | 4.39009e-10 |
| 7df21c836bec5751f83c0cce | bias1_profiled_removal | sphere_still | False | -18.9589 | 0.00159649 |
| 7df21c836bec5751f83c0cce | bias1_profiled_removal | flat_still | True | 0 | 5.70641e-12 |

The saved audit completed 48 affine solves across all 24 endpoints, with no original-recording reads, native predictions or optimizer starts. Its linear predictions cannot establish actual improvement or relabel any fit.

[Frozen audit scope](PLAN.md) · [Detailed interpretation](INTERPRETATION.md) · [Metrics CSV](primary-metrics.csv) · [Observed study](../ilvis0-horizontal-observed-20261018/README.md).
