# A small prediction pilot

Three stretches are selected for the next prediction test. Selection uses only
the saved eligibility and route metadata: IMU type, hemisphere, duration and
conservative flight group. It uses no gyro summary, model preference or fit cost.

| Recording | IMU type | Length | Mean latitude | Mean course |
|---|---:|---:|---:|---:|
| Ames 510, October 24 survey | 8 | 11.13 min | 62.65° S | 119.54° |
| Ames 610, March 22 survey | 21 | 7.27 min | 42.29° N | 8.73° |
| 610, October 29 survey | 21 | 11.15 min | 63.96° S | 191.67° |

The [selection CSV](selection.csv) preserves exact filenames, source hashes,
UTC intervals, speeds and group IDs. The three conservative groups are distinct;
this does not establish three independently verified instrument installations.
There is no northern IMU8 stretch in the eligible population.

The rule selects the longest stretch in each available IMU/hemisphere cell,
visiting cells with fewer eligible stretches first. Segment ID breaks duration
ties. A group already selected cannot contribute again. The source inventories
and selection have recorded hashes so that this choice can be reproduced.

This is a preparation inventory, not a completed prediction experiment. The
[pilot plan](PLAN.md) fixes 72 starts, both clocks, the error weights and numerical
limits. Exact receiver split boundaries are saved before fitting:

| Recording | GPS fixes for calibration | Later GPS fixes for scoring |
|---|---:|---:|
| Ames 510, October 24 survey | 445 | 223 |
| Ames 610, March 22 survey | 290 | 146 |
| 610, October 29 survey | 446 | 223 |

Training
will use the earlier part of each stretch. Later positions will only score the
continuous IMU forecast, including height. The numerical environment, exact
decoded inputs and qualified source hashes must be frozen before execution.
The [matched training/forecast controls](../ilvis0-near-zero-forecast-controls/README.md)
have passed all 24 cases. The pilot's 24 software checks also pass, including a
test that changed later GPS positions leave fitting and forecasting unchanged.
The [initial run](../ilvis0-retrospective-prediction-pilot/README.md) exposed a
missing compiled source before any numerical calculation. Its failures are
preserved. The [corrected packaging](LOADER_REPAIR.md) adds an isolated-loader
check and reuses the same decoded input bytes in a separate freeze.
All NASA splits remain retrospective development tests. Reserved ESA groups
are untouched.

[Prediction method](../PREDICTION_VALIDATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md)
