# Training cadence and fixed accepted alternatives

The preceding generated-data trial found allowed calibrations with later north
predictions about 23 m apart, exceeding its 20 m target in all six cases. This
diagnostic asks whether the gaps between its five earlier observations permit
those alternatives. It does not search for another fit or change a calibration bound.

## Fixed inputs and selection

Use the completed `ilvis0-feasible-step-controls-20261022` evidence. For each
of its three physical models and two processing cases, freeze three calibrations:
the original point and the saved feasible pair with the smallest and largest
later north predictions. These are software-diagnostic selections, not aircraft
selection or independent confirmation. Preserve source identities and hashes.

Use the same complete 96,000 IMU packets, physical scales, 27 calibration
coordinates, clock and compiler. An IMU is an inertial measurement unit containing
gyroscopes and accelerometers. No aircraft original or protected ESA group is read.

Evaluate each fixed point at **one-second spacing from 2 through 290 seconds**,
followed by the original 438-second prediction. This gives 289 training-time
predictions and one later prediction. All original times—2, 10, 30, 180, 290 and
438 seconds—must reproduce their saved values exactly. Adding output queries
must not change integration history. Preserve the native output and all Jacobian
columns before checking consistency.

## Comparison without fabricated observations

The original five noisy observations remain fixed and all chosen points must
satisfy them. At added times there are **no measured observations**. Compare
the three predicted positions by testing overlap of their ±1 m coordinate
intervals. Do not create noise or observations to make a model pass.

For a represented prediction range of width `d` on an axis, optimistic common
overlap is `2 × (1 m + guard) − d`; guaranteed common overlap is
`2 × (1 m − guard) − d`. Retain the existing 0.00001 m numerical guard as an
assumption, not a newly qualified floating-execution bound.

A negative optimistic overlap shows that no common observation can satisfy all
three predictions at that epoch under these assumptions. Nonnegative overlap
leaves that possibility open. It neither predicts actual noise nor proves that
every possible observation admits all three. Report each axis, first disjoint
epoch and minimum overlap; preserve incomplete and failed records.

## Finite execution

| Work | Maximum |
|---|---:|
| Fixed task starts | 18 |
| Native batches | 18 |
| Predictions per batch | 290 |
| Conservative packet visits | 501,120,000 |
| Optimizer starts | 0 |
| New observations | 0 |
| Numerical allocation | Four workers × one thread |
| Total cooperative clock allowance | 600 seconds |

Charge each 27,840,000-visit batch before execution. Check a 120-second
per-identity allowance cooperatively; individual calls finish without signals.
Freeze source, input and environment hashes before launch. No retries or budget
expansion. Use the common study runner and shared fixed-point evaluator.

Passing execution requires all 18 records to preserve their original epoch
values and source bindings. Whether overlap survives is the scientific-diagnostic
outcome, not a gate to be tuned. This study provides no outer prediction bound,
continuous-time coverage, empirical receiver-error law, new Earth-model comparison
or observed-data fit allowance. V01 remains unqualified.

Package all outcomes and exact overlap calculations from sealed artifacts without
refitting. Compact declared duplicate inputs and evidence through verified archive
aliases; retain original bytes and failures.
