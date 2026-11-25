# Changing the direction of a rejected solver step

The trial passed **4 of 8 known-answer cases**. The original solver and
the earlier shorter-step trial passed the same four. All eight cases ran to
a recorded result using 180 of the 320 allowed evaluations.

| Known optimum | Starts passed | What happened |
| --- | ---: | --- |
| Upper limit | 2 of 2 | Recovered the known objective and passed the fresh position check. |
| Lower limit | 2 of 2 | Recovered the known objective and passed the fresh position check. |
| Interior | 0 of 2 | Both stopped before stationarity and failed the fresh position check. |
| Weakly constrained direction | 0 of 2 | The solver accepted 17 corrected steps across the two starts, and both still failed the fresh position check. |

The correction uses the evaluated residual at a rejected point to estimate
how the residual bends along the step. It then adjusts the direction within
the same calibration bounds. The trial kept the stopping checks and
acceptance limits fixed. All four failed cases also exceeded the allowed
parameter and objective errors against the known answers.

The correction failed the gate for a generated flight-scale test. This
trial used no aircraft measurements, and the two unresolved ESA
development comparisons retain their recorded dispositions.

[Frozen plan](GEODESIC_STEP_PLAN.md) ·
[Per-start results](geodesic-step-controls-result.json) ·
[Verification](geodesic-step-controls-evidence/README.md)
