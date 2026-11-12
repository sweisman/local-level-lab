# Which generated IMU errors moved the forecast?

One preselected twenty-minute generated flight was replayed ten ways, using the same four random error arrays in every comparison. The generating calibration and starting state were supplied, and the complete noisy replay matched the earlier sealed oracle exactly.

| Error stream | Later horizontal RMS | Later height RMS |
|---|---:|---:|
| clean | 0.05 m | 0.06 m |
| full | 439.43 m | 4.73 m |
| only gyro white | 229.98 m | 14.03 m |
| only gyro bias | 376.21 m | 2.17 m |
| only accel white | 6.38 m | 2.24 m |
| only accel bias | 20.07 m | 9.46 m |

In this one generated case, the changing gyro bias and random gyro increments produce far larger horizontal errors than either accelerometer component. The clean stream misses by about 5 cm; the complete noisy stream misses by 439 m. These are simulated error settings, not measured specifications for an archive IMU.

The [finite plan](PLAN.md) also checks each component by removing it from the complete noisy stream. The saved report records those changes and the nonadditive interaction. These counterfactual effects are descriptive; nonlinear effects cannot be assigned uniquely to one sensor channel. No aircraft data or protected ESA confirmation group was used, and this is not an Earth-model decision.
