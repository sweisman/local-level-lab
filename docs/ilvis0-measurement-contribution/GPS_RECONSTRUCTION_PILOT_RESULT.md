# GPS processing changes short-window acceleration estimates

All **2,224 GPS solutions converged** at the 1,112 frozen epochs across
the two recordings. Each GPS solution used the first onboard position
as its starting guess. The later onboard positions entered only after
the solve, when the differences were calculated. No inertial
measurements were used.

| Recording | GPS method | Onboard position difference north / east / up, RMS | Vertical acceleration difference over 10 seconds, RMS | Vertical acceleration difference over 30 seconds, RMS |
|---|---|---:|---:|---:|
| IMU8, 669 epochs | L1 | 0.25 / 0.26 / 1.08 m | 0.0384 m/s² | 0.0030 m/s² |
| IMU8, 669 epochs | Dual frequency | 0.72 / 0.64 / 6.47 m | 0.0987 m/s² | 0.0087 m/s² |
| IMU21, 443 epochs | L1 | 0.29 / 0.28 / 0.39 m | 0.0171 m/s² | 0.0016 m/s² |
| IMU21, 443 epochs | Dual frequency | 0.55 / 0.38 / 4.38 m | 0.0492 m/s² | 0.0045 m/s² |

The vertical acceleration figures come from fitting a quadratic to the
height-difference series on fixed windows. The 30-second windows reduced
the disagreement by about 11 to 13 times. They also smooth real changes in
aircraft motion. A useful window needs both adequate duration and a bound
on the error from approximating the trajectory over that duration.

Dual-frequency code largely shifted the height downward, by 6.27 m on
average in the IMU8 recording and 4.32 m in the IMU21 recording. A constant
height shift alone does not produce an acceleration difference. The
remaining differences vary over time. The saved report includes exact
one-, five- and fifteen-second correlations.

This comparison measures how much the choice of GPS processing changes
the input to the inertial comparison. The GPS methods share measurements,
broadcast satellite data and atmospheric assumptions. Their agreement
leaves errors common to all three position streams unmeasured. The
solutions use the conventional GPS geometry and make no Earth-model
decision.

[Fixed plan](GPS_RECONSTRUCTION_PILOT_PLAN.md) ·
[Position comparisons](gps-reconstruction-pilot-positions.csv) ·
[Velocity and acceleration comparisons](gps-reconstruction-pilot-derivatives.csv) ·
[Verified receipt](gps-reconstruction-pilot-receipt.json).

Replay the reporting calculation from the sealed local study without
solving the positions again:

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.ilvis0_gps_reconstruction_pilot_report
```
