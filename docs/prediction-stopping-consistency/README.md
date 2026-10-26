# Why the numerical stopping check failed

The bounded diagnostic completed 4 of four saved-point checks.
It did not fit another model, change an acceptance limit or revise the original results.

| Saved point | Original fit passed | Repeatable | Derivatives agree at smallest step | Fresh stopping check |
|---|---|---|---|---|
| calibration-seed-281474976810725-increment-sphere_rotating-0-0 | Yes | Yes | No | Yes |
| calibration-seed-281474976810726-increment-sphere_rotating-0-0 | No | Yes | No | No |
| calibration-seed-281474976810726-increment-sphere_rotating-0-1 | No | Yes | No | No |
| calibration-seed-281474976810726-increment-sphere_rotating-1-0 | Yes | Yes | No | Yes |

Derivative agreement uses the unchanged predeclared software error scale as a diagnostic.
A disagreement on a native problem does not reclassify its fit or establish an alternative optimum.
The signed cost changes, derivative error curves and retained columns are available below.

[Summary CSV](results.csv) · [Derivative curves CSV](derivatives.csv) ·
[Frozen plan](../PREDICTION_STOPPING_PLAN.md) · [Previous phase](../PREDICTION_PHASE_RESULTS.md).

No calibrated uncertainty, aircraft result or new Earth-model conclusion follows from these checks.
