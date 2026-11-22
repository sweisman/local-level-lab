# The force ordering survived the carrier-phase motion check

On all **991 windows**, the shape that required more force stayed the same
when we substituted carrier-phase motion for onboard GPS motion. This held
under both packet clocks and both background-field assumptions. At every
window centre, the change in either candidate's force stayed within the
onboard globe–disc force difference.

| Recording and interval | Windows | 95th percentile of the change in a candidate's centre force |
|---|---:|---:|
| IMU8, training | 415 | 0.00274 m/s² |
| IMU8, later | 193 | 0.00603 m/s² |
| IMU21, training | 265 | 0.000860 m/s² |
| IMU21, later | 118 | 0.000110 m/s² |

With the original accelerometer gains held fixed, the number of later
lower-bound violations stayed the same for every candidate. IMU8 had three
to six violations per candidate across the 386 later window–clock checks.
IMU21 had zero across 236. On the IMU8 training portion, the carrier-phase
path introduced six violations per candidate across 830 checks, compared
with zero using onboard motion. This count describes overlapping windows
and two clock assumptions for one recording.

The [frozen calculation](GPS_CARRIER_FORCE_PLAN.md) keeps the original
position at each window centre, the same model equations, and the same
whole-packet intervals. It uses saved phase displacements and no new
position or inertial fits. The result measures sensitivity to a change in
GPS motion. Errors shared by onboard GPS and carrier phase remain open, as
does matching the full accelerometer history under one calibration.

[Window results](gps-carrier-force-windows.json.gz) ·
[Verification receipt](gps-carrier-force-receipt.json).

```sh
~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- \
  env PYTHONPATH=analysis ~/venv/bin/python -m lll.ilvis0_carrier_force replay
```
