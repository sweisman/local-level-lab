# Evidence for docs/METHODOLOGY.md

**Historical evidence notice (software 0.6.0):** the tables below predate the corrected crab objective,
calibration covariance and pilot-2 gates. They are not validation of the current release. The pooling
coverage figure in §9 measured ±2 standard errors, not the reported t-based interval. Full evidence
regeneration and tail campaigns require separate approval; see [VALIDATION.md](VALIDATION.md)
and [PRIMARY_CORPUS.md](PRIMARY_CORPUS.md). Small 0.6.0 pilot results, when generated, are
stored separately and do not replace the historical tables or establish tail calibration.

Regenerate with `python analysis/tests/evidence.py`.

## 1. lll.models against independent geometry

Largest difference over 5 states × 3 models: 8.6e-12 rad/s (1.8e-06 °/h).

## 2. What a single flight can identify (truth: still globe)

| route | bias-likeness k_curv | bias-likeness k_disc | k_curv | wrong models rejected | flagged not identified |
|---|---|---|---|---|---|
| north, east, south | 0.92 | 0.45 | 0.97 ± 0.94 | 1 of 2 | no |
| zigzag 60°/100°/20° | 0.98 | 0.93 | 0.84 ± 0.95 | 1 of 2 | yes |
| straight, no IMU turns | 1.00 | 0.99 | 1.01 ± 1.06 | 1 of 2 | yes |
| straight, IMU turned about the vertical ×3 | 0.67 | 0.99 | 1.11 ± 0.17 | 2 of 2 | no |
| straight, IMU flipped ×3 | 1.00 | 1.00 | 1.08 ± 0.76 | 0 of 2 | yes |

## 3. Ground calibration: horizontal rate against g-sensitivity

| truth | sequence | g-sensitivity up to 40 °/h/g | horizontal measured (°/h) | predicted | vertical measured | predicted |
|---|---|---|---|---|---|---|
| sphere_rotating | single | no | 13.11 ± 1.21 | 11.44 | 9.77 | 9.77 |
| sphere_rotating | single | yes | 12.94 ± 1.34 | 11.44 | 49.34 | 9.77 |
| sphere_rotating | palindrome | no | 11.43 ± 1.39 | 11.44 | 10.09 | 9.77 |
| sphere_rotating | palindrome | yes | 11.80 ± 1.15 | 11.44 | 50.58 | 9.77 |
| flat_still | single | no | 0.00 ± 1.37 | 0.00 | -0.26 | 0.00 |
| flat_still | single | yes | 1.00 ± 1.26 | 0.00 | 39.85 | 0.00 |
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

By design, drift and position effects are separated, so g-sensitivity alone can't move the fitted drift. What moves it here is quantization: coarse counts interact with constant offsets. Compare the z column with and without g-sensitivity at each range.

## 5. Temperature

|  | with term | without |
|---|---|---|
| coefficient (°/h/°C), injected 1.0, −0.8, 0.6 | 0.98, -0.77, 0.72 | – |
| noise per 60-s bin (°/h) | 1.39 | 2.12 |
| k_curv | 1.19 ± 0.99 | 2.39 ± 0.95 |

## 6. Mount slip watchdog

| true slip (°/h) | measured, WMM declination (per segment) | measured, no declination model (cross-check) | segments left out |
|---|---|---|---|
| 0.0 | -0.1, -0.2, -0.1 | 2.7, 3.3, 0.9 | none |
| 2.0 | 2.0, 1.8, 1.9 | 4.7, 5.3, 2.9 | [0, 1, 2] |
| 3.0 | 3.0, 2.8, 2.9 | 5.7, 6.3, 3.9 | [0, 1, 2] |
| 8.0 | 8.0, 7.7, 7.8 | 10.6, 11.2, 8.8 | [0, 1, 2] |

The WMM version decides, at 1.5 °/h. The cross-check reads the route's declination change as slip.

## 7. Hard conditions: the true model is never rejected

| condition | truth | truth rejected? | models rejected | largest |k − true| / σ |
|---|---|---|---|---|
| adverse flight (temperature, turbulence, tilt slip, climb/descent, GNSS gaps) | sphere_rotating | no | sphere_still, flat_still | 1.0 |
| adverse flight (temperature, turbulence, tilt slip, climb/descent, GNSS gaps) | sphere_still | no | sphere_rotating, flat_still | 1.5 |
| adverse flight (temperature, turbulence, tilt slip, climb/descent, GNSS gaps) | flat_still | no | sphere_rotating | 0.7 |
| hardware faults (all at once) | sphere_rotating | no | sphere_still, flat_still | 1.4 |
| hardware faults (all at once) | sphere_still | no | sphere_rotating, flat_still | 2.1 |
| hardware faults (all at once) | flat_still | no | sphere_rotating | 2.2 |

## 8. Five-hour single-heading cruise

|  | bias-likeness k_curv | k_curv (truth 1) | models rejected (truth: still globe) |
|---|---|---|---|
| no IMU turns | 1.00 | 1.32 ± 0.80 | sphere_rotating |
| IMU turned about the vertical hourly | 0.71 | 1.33 ± 0.29 | sphere_rotating, flat_still |

## 9. Pooling when units differ

| method | 95 % interval covers the truth |
|---|---|
| random effects (REML, Hartung–Knapp), sessions → units → population | 91 % |
| fixed effects (all sessions as independent) | 23 % |

8 units × 4 sessions, unit offsets σ = 0.3, session errors σ = 0.1.

## 10. IMU turns measured by the gyro

Measured turn angles (true 180°): 179.93°, 179.96°, 179.98°

## 11. Crab angle (fuselage off the GNSS track)

| truth | crab | truth rejected? | k_rot | k_curv | k span over crab priors (σ) | crab-sensitive flag? |
|---|---|---|---|---|---|---|
| sphere_rotating | none | no | 1.06 ± 0.19 | 0.92 ± 0.28 | 1.78 | yes |
| sphere_rotating | 8°, no crab term | YES | 0.63 ± 0.11 | 1.51 ± 0.15 | – | no |
| sphere_rotating | 8°, crab term (5° prior) | no | 0.63 ± 0.20 | 1.54 ± 0.28 | 0.35 | no |
| sphere_still | none | no | -0.08 ± 0.12 | 1.11 ± 0.17 | 0.97 | no |
| sphere_still | 8°, no crab term | no | -0.19 ± 0.10 | 1.25 ± 0.14 | – | no |
| sphere_still | 8°, crab term (5° prior) | no | -0.22 ± 0.12 | 1.29 ± 0.16 | 0.76 | no |

Straight route with three same-side-up IMU turns. A flat truth has no horizontal signal, so crab doesn't affect it.

Crab-prior sweep with 8° of true crab (k_rot / k_curv):

| truth | 3° prior | 5° prior | 10° prior | 15° prior |
|---|---|---|---|---|
| sphere_rotating | 0.63 / 1.54 | 0.63 / 1.54 | 0.65 / 1.51 | 0.70 / 1.44 |
| sphere_still | -0.20 / 1.27 | -0.22 / 1.29 | -0.26 / 1.35 | -0.29 / 1.38 |

## 12. BLE timing under lost notifications

| notification loss | samples lost | detected | timing error, 95th percentile (ms) |
|---|---|---|---|
| 0.0 % | 0 | 0 | 0.0 |
| 0.1 % | 178 | 178 | 0.0 |
| 1.0 % | 1781 | 1779 | 11.8 |
| 3.0 % | 5301 | 5296 | 22.4 |

30 min at 100 Hz, 7.5-ms connection interval.

## 13. Reversal test with strong g-sensitivity

| truth | pairs | horizontal rate (°/h) | predicted | repeatability σ (°/h) |
|---|---|---|---|---|
| sphere_rotating | 6 | 11.07 ± 0.72 | 11.44 | 1.25 |
| flat_still | 6 | 0.00 ± 0.64 | 0.00 | 0.92 |
