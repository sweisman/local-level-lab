# Shape-first refinement results

Six recordings, four matched assumption cases each: 40/72 fits converged, 0 failed. 73 starts were charged, including 1 interrupted starts without a retained final fit.

These are conditional local fits, not a calibrated detection or a guarantee of global minima. Constant fitted offsets are not measured time-varying IMU drift. The offset assumptions are ±0.1 and ±1 degree/hour, each tested with zero or freely fitted common Earth-rate removal.

| Recording | Shape preference across all cases | Converged fits | Rotation diagnostics |
|---|---|---:|---|
| ILVIS0_gyro_54935_lvis_applanix_POSAV.013 | unresolved | 1/12 | withheld |
| ILVIS0_applanix_56916_510_POS510.013 | unresolved | 9/12 | withheld |
| ILVIS0_applanix_55495_20101026_510_lvis_LVIS.013 | globe | 12/12 | available conditionally |
| ILVIS0_applanix_55520_20101120_510_lvis_LVIS.013 | unresolved | 2/12 | withheld |
| ILVIS0_applanix_57289_510_LVISGH.013 | globe | 12/12 | available conditionally |
| ILVIS0_58016_B200T_N44U_imu_510i_0539_41265390920_104746.013 | unresolved | 4/12 | withheld |

[Shape contrasts](shape.csv) are reported first. [Rotation contrasts](rotation.csv) contain only recordings whose shape comparisons consistently favor globe after convergence in every case. An empty rotation table means that stage remained withheld. [Fit details](fits.csv) preserve convergence, fitted constant offsets, boundary hits and failures.

All scientific decisions abstain. Instrument processing, calibration, clock and receiver uncertainty remain partly assumed. Fused navigation never serves as an independent observation. The six recordings are development cases, not six independent validation trials.

The original data and older freezes remain unchanged. No further fit, synthetic campaign or calibrated-policy promotion is performed by this report. See the [refinement methods and limitations](README.md) before interpreting a preference.
