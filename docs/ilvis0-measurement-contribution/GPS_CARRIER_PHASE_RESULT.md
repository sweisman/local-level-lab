# Carrier-phase motion agrees most closely with onboard GPS

The phase calculation recovered displacement for **1,109 of 1,110 adjacent
pairs**. One IMU8 pair spanned a missing receiver epoch. All 991 original
30-second accelerometer windows had complete phase support. No inertial
measurements entered the calculation, and no inertial fits were started.

The table gives the RMS difference in vertical acceleration between the
phase-derived motion and each position stream, in m/s².

| Recording and interval | Windows | Onboard GPS | L1 code | Dual-frequency code |
|---|---:|---:|---:|---:|
| IMU8, training | 415 | 0.00108 | 0.00324 | 0.00832 |
| IMU8, later | 193 | 0.00197 | 0.00356 | 0.00953 |
| IMU21, training | 265 | 0.000278 | 0.00174 | 0.00449 |
| IMU21, later | 118 | 0.0000580 | 0.00128 | 0.00502 |

On both recordings, onboard GPS gave the closest match to carrier-phase
motion in the vertical direction. The two recordings differed in the size
of that agreement. Their median within-pair satellite range-change
residuals were about 2.4 mm and 2.3 mm. Those residuals measure consistency
among the satellite observations given the fitted displacement and clock
change. The onboard and phase estimates come from the same receiver and
share satellite and propagation errors. This check gives no absolute
acceleration error or coverage guarantee.

The [frozen plan](GPS_CARRIER_PHASE_PLAN.md) keeps the original epochs and
training split. It uses the earlier L1 code position as an anchor and
checks the phase sign against earlier code changes. The phase solver uses
later code for signal travel time. Comparisons with onboard and code
positions are calculated after each phase solve.

[Verified receipt](gps-carrier-pilot-receipt.json) ·
[Per-pair results](gps-carrier-pair-results.json.gz) ·
[Matched motion windows](gps-carrier-matched-windows.json.gz).

Replay the report from the [archived study](../ilvis0-gps-carrier-pilot-runtime/README.md)
without solving again:

```sh
~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- \
  env PYTHONPATH=analysis ~/venv/bin/python -m lll.ilvis0_gps_carrier_report
```
