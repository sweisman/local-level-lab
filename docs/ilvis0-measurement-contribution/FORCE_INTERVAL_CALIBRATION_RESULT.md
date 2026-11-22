# One gain left a gap in every force-interval comparison

None of the **24 profiles** could make every training force interval overlap
using one gain in the original 0–15% range. The smallest uniform separation
that had to be covered ranged from **0.0487 to 0.0838 m/s²**. This includes
profiles using onboard motion, carrier-phase motion, and both paths together.
The earlier lower-bound check tested only one end of the interval.

The table shows the profiles requiring one gain to cover both GPS paths.
The gap is the largest separation between the measured and scaled predicted
force intervals. The gain is fitted on training windows and left fixed later.

| Recorder | Candidate | Training gain | Training gap, m/s² | Later gap, m/s² | Later checks outside the training gap |
|---|---|---:|---:|---:|---:|
| IMU8 | Globe, specified field | 0% | 0.0606 | 0.0624 | 4 / 772 |
| IMU8 | Globe, zero field | 0% | 0.0744 | 0.0763 | 4 / 772 |
| IMU8 | Disc, specified field | 0.482% | 0.0506 | 0.0510 | 2 / 772 |
| IMU8 | Disc, zero field | 0% | 0.0838 | 0.0856 | 4 / 772 |
| IMU21 | Globe, specified field | 0% | 0.0726 | 0.0530 | 0 / 472 |
| IMU21 | Globe, zero field | 0% | 0.0734 | 0.0538 | 0 / 472 |
| IMU21 | Disc, specified field | 0% | 0.0781 | 0.0583 | 0 / 472 |
| IMU21 | Disc, zero field | 0% | 0.0816 | 0.0619 | 0 / 472 |

Seven joint profiles reached the lower gain limit. The result applies to the
nonnegative gain range and the saved trajectories. It does not identify how
much of the gap comes from trajectory approximation, gravity assumptions,
receiver error or accelerometer calibration. These repeated checks describe
two recordings. The training gap is an observed maximum and supplies no
calibrated coverage threshold or shape decision.

The measured upper endpoint bounds the magnitude of each packet's averaged
force vector. A bound on direction change within packets is needed to turn
that endpoint into an upper bound on the continuous force magnitude. The
two-sided comparison here is therefore a diagnostic of the saved packet
and trajectory approximations. [Force averaging](FORCE_AVERAGING.md).

[Frozen calculation](FORCE_INTERVAL_CALIBRATION_PLAN.md) ·
[All 24 profiles](force-interval-calibration-receipt.json).

```sh
~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- \
  env PYTHONPATH=analysis ~/venv/bin/python -m lll.ilvis0_force_interval_calibration replay
```
