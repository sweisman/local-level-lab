# Saved calibration-constraint audit

48/48 saved-sector audits pass; state: complete.

Every row preserves all 27 nuisance coordinates. These are generated calibration ranges under necessary constraints, not measured device performance or independent aircraft observations.

| Parameter | Sectors examined | Further narrowed | Median ratio to row-contracted width |
|---|---:|---:|---:|
| attitude_x | 48 | 0 | 1.000000 |
| attitude_y | 48 | 0 | 1.000000 |
| attitude_z | 48 | 0 | 1.000000 |
| velocity_x | 48 | 0 | 1.000000 |
| velocity_y | 48 | 0 | 1.000000 |
| velocity_z | 48 | 0 | 1.000000 |
| position_x | 48 | 7 | 1.000000 |
| position_y | 48 | 6 | 0.999999 |
| position_z | 48 | 0 | 1.000000 |
| gyro_bias_x | 48 | 0 | 1.000000 |
| gyro_bias_y | 48 | 0 | 1.000000 |
| gyro_bias_z | 48 | 0 | 1.000000 |
| accel_bias_x | 48 | 0 | 1.000000 |
| accel_bias_y | 48 | 0 | 1.000000 |
| accel_bias_z | 48 | 0 | 1.000000 |
| gyro_gain_x | 48 | 0 | 1.000000 |
| gyro_gain_y | 48 | 0 | 1.000000 |
| gyro_gain_z | 48 | 0 | 1.000000 |
| accel_gain_x | 48 | 0 | 1.000000 |
| accel_gain_y | 48 | 0 | 1.000000 |
| accel_gain_z | 48 | 0 | 1.000000 |
| lever_x | 48 | 0 | 1.000000 |
| lever_y | 48 | 0 | 1.000000 |
| lever_z | 48 | 0 | 1.000000 |
| gravity_delta | 48 | 0 | 1.000000 |
| time_offset | 48 | 0 | 1.000000 |
| earth_removal | 48 | 0 | 1.000000 |

| Case | Sectors | Existing nonlinear floor exceeds target N / E / height |
|---|---:|---|
| case-0-0-400 | 8 | 0 / 0 / 8 |
| case-0-1-400 | 8 | 0 / 0 / 8 |
| case-1-0-400 | 8 | 0 / 0 / 8 |
| case-1-1-400 | 8 | 0 / 0 / 8 |
| case-2-0-400 | 8 | 0 / 0 / 8 |
| case-2-1-400 | 8 | 0 / 0 / 8 |

A floor applies to the retained computed remainder, not to true aircraft uncertainty. Recomputing a rigorously smaller remainder could change it; a better linear optimizer alone cannot erase it. LP failure uses the qualified full-box fallback. No rank threshold drops unidentified columns.

Reserved/used identities: 48/48; completed LP proposals: 2592. Zero native integration, Earth-model fits or original-file reads.

[All parameter intervals](parameters.csv) · [Frozen scope](PLAN.md) · [Source comparison](../ilvis0-regrouped-cover/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
