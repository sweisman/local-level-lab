# Why the height-only fitting control stalled

The proposed correction is too large for its local linear approximation.
Changing the numerical column scaling does not fix it. This explains a concrete
obstacle in the generated-motion control; it changes no recorded-flight result.

## What the diagnostic measured

The failed endpoint reproduced exactly on repeated evaluation. Its cost remains
about **0.00000001985** and its stationarity measure remains **0.0001409**, above
the unchanged **0.0001** limit. All 33 planned evaluations completed, with no
optimizer starts or original-recording reads.

At that point the bounded linear calculation proposes large, compensating
changes in calibration and initial velocity. Its largest normalized changes
are almost two units: nearly the whole permitted range. It predicts a cost
near **0.00000000000167**. The actual nonlinear calculation instead gives
**0.02355**, about **1.2 million times worse** than the starting cost.

Even one-sixteenth of that correction increases the cost, to about
**0.0000005492**, and worsens stationarity. The unscaled and column-scaled
formulations give essentially identical corrections and outcomes. Simple
rescaling is therefore insufficient at this endpoint.

## Which quantities trade off

The weakest local direction mainly trades Z gyro offset against eastward initial
velocity. Another weak direction is dominated by timing offset. These directions
refer to normalized parameters under the declared bounds, not equal physical
units or estimated uncertainty intervals.

The columns responsible for the current stationarity failure are primarily
initial velocity and gravity, with initial pitch also above the limit. This
distinguishes the directions that are weakly measured from the gradient that
currently blocks acceptance. All six columns were retained.

Central differences at two step sizes closely reproduce the strong gravity,
velocity and pitch derivatives. Weak timing and gyro-offset differences are
more sensitive to numerical subtraction: the timing-column relative difference
is about 0.37% at the larger step and 3.9% at the smaller one. These checks do
not establish arbitrary precision in the weakest derivatives.

The independent continuous-motion generating parameters do not give an exact
zero residual in the discrete navigation calculation. Its finite integration
error was already part of these controls. The generated trajectory provides
an external prediction check; its parameters are not asserted to be the exact
optimum of the approximate inverse problem.

## Next candidate

Test a bounded trust-region correction that limits how far the local linear
model is used. Keep every parameter, the original physical bounds and the
fresh stationarity/cost/retained-position limits. A new candidate needs its own
constructed controls and separately frozen generated-motion qualification,
including different starts. Neither a small residual nor one successful
diagnostic probe can replace that qualification.

The earlier failed qualification remains failed, its eighteen unrun controls
remain untested, and observed refits remain blocked. The complete archival
comparison remains **53 globe / 0 flat / 0 unresolved**.

[Measured correction table](README.md) · [Fixed diagnostic scope](PLAN.md) ·
[Prior qualification](../ilvis0-projected-fitting-controls-20261018/INTERPRETATION.md).
