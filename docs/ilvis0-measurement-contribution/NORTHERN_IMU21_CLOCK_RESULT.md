# Clock choice explains two decoder failures, and the original gate remains closed

All four elapsed-clock results reproduced the earlier engineering checks.
Using the same packets with a nominal 5 ms period cleared two of the three
failures. The original failing representative still failed its chronological
gyro scale check. The 0.1% scale tolerance and the original comparison dates
stay fixed.

| File date | Median header period relative to 5 ms | Elapsed-clock failure | Nominal-clock result |
|---|---:|---|---|
| 2009-10-13 | +33 ppm | Gyro chronological scale | Gyro chronological scale still failed |
| 2009-10-31 | −959 ppm | Gyro and accelerometer scale | Both channels passed |
| 2010-04-09 | +1,020 ppm | Accelerometer scale | Both channels passed |
| 2010-04-22 | +32 ppm | Both channels passed | Both channels passed |

The largest chronological gyro discrepancy on the original failed date was
0.114% under elapsed timing and 0.146% under nominal timing. Each diagnostic
used the same raw increments, axis mapping and matched fused-navigation
reference. Clock sensitivity explains the two reversals in the engineering
check. The evidence leaves the actual IMU integration time and the cause of
the original representative's failure open.

All four northern analysis stretches use this IMU21 configuration. Three
pass their individual saved file checks. None meets the existing two-date
configuration rule. This four-file, zero-fit engineering check changes no
eligibility and leaves the original result intact.

[Frozen plan](NORTHERN_IMU21_CLOCK_PLAN.md) · [Receipt](northern-imu21-clock-receipt.json) ·
[Original decoder study](../ilvis0-imu21-assessment-20261007/README.md).

From the repository root with the four original sources available, replay with

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.ilvis0_imu21_clock_diagnostic replay
```
