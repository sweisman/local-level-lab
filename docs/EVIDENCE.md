# Evidence for docs/METHODOLOGY.md

Regenerate with `python analysis/tests/evidence.py`.

## 1. lll.models against independent geometry

Largest difference over 5 states × 3 models: 8.6e-12 rad/s (1.8e-06 °/h).

## 2. What a single flight can identify (truth: still globe)

| route | bias-likeness k_curv | bias-likeness k_disc | k_curv | wrong models rejected | flagged not identified |
|---|---|---|---|---|---|
| north, east, south | 0.92 | 0.45 | 0.79 ± 0.98 | 1 of 2 | no |
| zigzag 60°/100°/20° | 0.98 | 0.93 | 0.74 ± 0.98 | 1 of 2 | yes |
| straight, no IMU turns | 1.00 | 0.99 | 0.82 ± 1.03 | 1 of 2 | yes |
| straight, IMU turned about the vertical ×3 | 0.68 | 0.99 | 1.08 ± 0.15 | 2 of 2 | no |
| straight, IMU flipped ×3 | 1.00 | 1.00 | 1.02 ± 0.74 | 1 of 2 | yes |

## 3. Ground calibration: horizontal rate against g-sensitivity

| truth | sequence | g-sensitivity up to 40 °/h/g | horizontal measured (°/h) | predicted | vertical measured | predicted |
|---|---|---|---|---|---|---|
| sphere_rotating | single | no | 13.03 ± 1.21 | 11.44 | 9.77 | 9.77 |
| sphere_rotating | single | yes | 12.90 ± 1.34 | 11.44 | 49.34 | 9.77 |
| sphere_rotating | palindrome | no | 11.28 ± 1.39 | 11.44 | 10.09 | 9.77 |
| sphere_rotating | palindrome | yes | 11.68 ± 1.15 | 11.44 | 50.58 | 9.77 |
| flat_still | single | no | 1.53 ± 1.37 | 0.00 | -0.26 | 0.00 |
| flat_still | single | yes | 1.67 ± 1.26 | 0.00 | 39.85 | 0.00 |
| flat_still | palindrome | no | 0.00 ± 1.12 | 0.00 | 0.68 | 0.00 |
| flat_still | palindrome | yes | 0.00 ± 1.37 | 0.00 | 40.55 | 0.00 |

## 4. 16-bit quantization of the gyro

| gyro range | one count (°/h) | g-sensitivity | fitted drift x, y, z (°/h per h) |
|---|---|---|---|
| ±2000 °/s | 220 | no | 7.2, -5.7, 6.1 |
| ±2000 °/s | 220 | yes | 7.7, -6.0, 15.4 |
| ±500 °/s | 55 | no | 6.5, -8.6, 7.8 |
| ±500 °/s | 55 | yes | 6.7, -8.6, 9.5 |
| ±250 °/s | 27 | no | 8.1, -8.5, 8.9 |
| ±250 °/s | 27 | yes | 7.1, -8.3, 9.6 |

By design, drift and position effects are separated, so g-sensitivity alone can't move the fitted drift. What moves it here is quantization: coarse counts interact with constant offsets. The shift shrinks with finer counts (z: 9.3 at ±2000 °/s, 1.7 at ±500, 0.7 at ±250 °/h per h).

## 5. Temperature

|  | with term | without |
|---|---|---|
| coefficient (°/h/°C), injected 1.0, −0.8, 0.6 | 0.98, -0.78, 0.72 | – |
| noise per 60-s bin (°/h) | 1.39 | 2.12 |
| k_curv | 1.16 ± 0.98 | 1.38 ± 0.96 |

## 6. Mount slip watchdog

| true slip (°/h) | measured, WMM declination (per segment) | measured, no declination model | segments left out |
|---|---|---|---|
| 0.0 | -0.1, -0.2, -0.1 | 2.7, 3.3, 0.9 | none |
| 2.0 | 2.0, 1.8, 1.9 | 4.7, 5.3, 2.9 | none |
| 3.0 | 3.0, 2.8, 2.9 | 5.7, 6.3, 3.9 | [0, 1, 2] |
| 8.0 | 8.0, 7.7, 7.8 | 10.6, 11.2, 8.8 | [0, 1, 2] |

## 7. Hard conditions: the true model is never rejected

| condition | truth | truth rejected? | models rejected | largest |k − true| / σ |
|---|---|---|---|---|
| adverse flight (temperature, turbulence, tilt slip, climb/descent, GNSS gaps) | sphere_rotating | no | sphere_still, flat_still | 0.4 |
| adverse flight (temperature, turbulence, tilt slip, climb/descent, GNSS gaps) | sphere_still | no | sphere_rotating, flat_still | 0.9 |
| adverse flight (temperature, turbulence, tilt slip, climb/descent, GNSS gaps) | flat_still | no | sphere_rotating | 0.4 |
| hardware faults (all at once) | sphere_rotating | no | sphere_still, flat_still | 2.3 |
| hardware faults (all at once) | sphere_still | no | sphere_rotating, flat_still | 2.3 |
| hardware faults (all at once) | flat_still | no | sphere_rotating | 2.3 |

## 8. Five-hour single-heading cruise

|  | bias-likeness k_curv | k_curv (truth 1) | models rejected (truth: still globe) |
|---|---|---|---|
| no IMU turns | 1.00 | 1.28 ± 0.78 | sphere_rotating |
| IMU turned about the vertical hourly | 0.71 | 1.32 ± 0.22 | sphere_rotating, flat_still |

## 9. Pooling when units differ

| method | 95 % interval covers the truth |
|---|---|
| random effects, sessions → units → population | 90 % |
| fixed effects (all sessions as independent) | 23 % |

8 units × 4 sessions, unit offsets σ = 0.3, session errors σ = 0.1.

## 10. IMU turns measured by the gyro

Measured turn angles (true 180°): 179.93°, 179.96°, 179.98°

