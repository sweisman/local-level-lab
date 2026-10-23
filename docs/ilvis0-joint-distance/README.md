# Adding accumulated IMU error to the same saved-trajectory comparison

**24/24 calculations completed.** The trajectories and receiver assumptions are unchanged. This adds two declared linear-noise examples, without refitting a parameter.

An IMU is an inertial measurement unit. Its random turning and acceleration errors can accumulate into position error. The examples below use isotropic acceleration power density 1e-8 m²/s³ and gyro power densities 1e-12 or 1e-10 rad²/s. **These are software sensitivity settings, not measured instrument specifications.** The fixed coupling and zero-time noise origin are assumptions of this linear example.

| Model | Processing | Receiver correlation (s) | Gyro PSD (rad²/s) | Receiver-only distance | Distance with added IMU noise |
|---|---|---:|---:|---:|---:|
| Globe + field | Zero removal | 10 | 1e-12 | 7.120 | 5.366 |
| Globe + field | Zero removal | 10 | 1e-10 | 7.120 | 2.905 |
| Globe + field | Zero removal | 300 | 1e-12 | 8.244 | 6.654 |
| Globe + field | Zero removal | 300 | 1e-10 | 8.244 | 3.505 |
| Globe + field | Profiled removal | 10 | 1e-12 | 7.135 | 5.388 |
| Globe + field | Profiled removal | 10 | 1e-10 | 7.135 | 2.888 |
| Globe + field | Profiled removal | 300 | 1e-12 | 8.269 | 6.713 |
| Globe + field | Profiled removal | 300 | 1e-10 | 8.269 | 3.480 |
| Globe, zero field | Zero removal | 10 | 1e-12 | 7.098 | 5.353 |
| Globe, zero field | Zero removal | 10 | 1e-10 | 7.098 | 2.898 |
| Globe, zero field | Zero removal | 300 | 1e-12 | 8.230 | 6.633 |
| Globe, zero field | Zero removal | 300 | 1e-10 | 8.230 | 3.496 |
| Globe, zero field | Profiled removal | 10 | 1e-12 | 7.112 | 5.373 |
| Globe, zero field | Profiled removal | 10 | 1e-10 | 7.112 | 2.880 |
| Globe, zero field | Profiled removal | 300 | 1e-12 | 8.254 | 6.691 |
| Globe, zero field | Profiled removal | 300 | 1e-10 | 8.254 | 3.471 |
| Stationary disc | Zero removal | 10 | 1e-12 | 4.906 | 4.025 |
| Stationary disc | Zero removal | 10 | 1e-10 | 4.906 | 1.447 |
| Stationary disc | Zero removal | 300 | 1e-12 | 6.381 | 4.497 |
| Stationary disc | Zero removal | 300 | 1e-10 | 6.381 | 1.526 |
| Stationary disc | Profiled removal | 10 | 1e-12 | 4.912 | 4.039 |
| Stationary disc | Profiled removal | 10 | 1e-10 | 4.912 | 1.450 |
| Stationary disc | Profiled removal | 300 | 1e-12 | 6.409 | 4.526 |
| Stationary disc | Profiled removal | 300 | 1e-10 | 6.409 | 1.526 |

Every comparison checks that adding an independent positive noise covariance cannot increase the noise-scaled separation of the same deterministic means. Raw position differences remain identical. The distances are not p-values, actual likelihood ratios or Earth-model votes.

This checks a supplied constant-coupling linear law. It does not establish the actual IMU noise, its independence, trajectory-dependent propagation, complete nonlinear calibration uncertainty or observational coverage. **V01 remains unqualified.** The 53-stretch findings and protected ESA data are unchanged.

[Frozen scope](PLAN.md) · [Receiver-only comparison](../ilvis0-receiver-distance/README.md) · [Error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md)
