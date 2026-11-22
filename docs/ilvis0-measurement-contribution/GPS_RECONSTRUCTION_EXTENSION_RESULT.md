# GPS processing differences persist across four NASA flight groups

Both GPS methods converged at every one of the 1,124 selected epochs on
two additional flights. That adds 2,248 verified position solutions to the
[earlier two-group comparison](GPS_RECONSTRUCTION_PILOT_RESULT.md). Each
solve used the same initial position for its recording. The comparison
used both sets of reconstructed positions and the onboard GPS positions.
It used no inertial measurements.

| Additional flight | GPS method | Position difference north / east / up, RMS | Vertical acceleration difference over 10 seconds, RMS | Over 30 seconds, RMS |
|---|---|---:|---:|---:|
| IMU8, 586 epochs | L1 | 0.42 / 0.24 / 0.98 m | 0.0340 m/s² | 0.0033 m/s² |
| IMU8, 586 epochs | Dual frequency | 0.72 / 0.70 / 1.82 m | 0.0870 m/s² | 0.0081 m/s² |
| IMU21, 538 epochs | L1 | 0.30 / 0.41 / 1.47 m | 0.0267 m/s² | 0.0032 m/s² |
| IMU21, 538 epochs | Dual frequency | 0.64 / 0.51 / 2.87 m | 0.0860 m/s² | 0.0073 m/s² |

Using 30-second windows instead of 10-second windows reduced the vertical
acceleration differences by factors of 8 to 12 on the added flights. That
averaging also smooths real motion. The observed differences quantify
processing sensitivity on the four southern flight groups. The methods
share GPS observations and modeling assumptions, so these differences
leave common errors unmeasured. Matching the reconstructed tracks to
the raw inertial packets on the added flights is a separate step.

All 12 blocks passed in 6.9 seconds on two threads. Seven focused checks
passed. The report verified the solve charges, original measurement
identities, retained receiver epochs and position differences.

[Frozen plan](GPS_RECONSTRUCTION_EXTENSION_PLAN.md) ·
[Selected epochs](gps-reconstruction-extension-selection.json) ·
[Position comparisons](gps-reconstruction-extension-positions.csv) ·
[Velocity and acceleration comparisons](gps-reconstruction-extension-derivatives.csv) ·
[Reproduction bundle](gps-reconstruction-extension-evidence/bundle.zip)
