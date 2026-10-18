# Generated-motion receiver refitting controls

**Not qualified:** 24/25 controls passed. No archival recording was read and no observed-data fit was started.

The batch stops at its first failed control. 18 planned controls were not run; they are neither passes nor measured failures.

The batch used 7 generated-motion starts and 459 native sweeps within its frozen 24-start / 2,400-sweep allowance.

| Model | Clock | Scored coordinates | Start | Pass | Maximum retained error (mm) | Maximum all-axis error (m) | Rank / columns |
|---|---|---|---|---|---:|---:|---:|
| sphere_rotating | nominal | latitude/longitude | zero | True | 0.004015 | 0.2298 | 6 / 6 |
| sphere_still | nominal | latitude/longitude | zero | True | 0.004552 | 0.7144 | 6 / 6 |
| flat_still | nominal | latitude/longitude | zero | True | 0.005023 | 0.827 | 5 / 6 |
| sphere_rotating | variable | latitude/longitude | zero | True | 0.005492 | 0.01794 | 6 / 6 |
| sphere_still | variable | latitude/longitude | zero | True | 0.005517 | 0.0565 | 6 / 6 |
| flat_still | variable | latitude/longitude | zero | True | 0.00553 | 3.456 | 5 / 6 |
| sphere_rotating | nominal | height | zero | False | 0.0006115 | 10.69 | 6 / 6 |

Pass requires the fresh numerical checks, retained error below 2 mm and objective recovery against independently generated truth. Unscored coordinates can move substantially; their errors are shown, not treated as measured constraints. All parameter columns are retained. Short generated controls do not demonstrate unique calibration, empirical uncertainty or Earth-model discrimination.

A failed batch blocks observed refits. A passing batch would qualify this interface and these cases only. Observed refits still need a separate finite freeze, matched candidates, repeats and an explicitly qualified retained-coordinate stopping policy. The published 53/0/0 comparisons are unchanged.

[Scope and limits](PLAN.md) · [Measurement-contribution work](../ilvis0-measurement-contribution/README.md).
