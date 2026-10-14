# Derivative and integration precision at fixed endpoints

The preceding [six-endpoint diagnostic](../ilvis0-shared-leg-probes-20261014/README.md)
found identical repeated predictions and near-identical value/tangent outputs,
while several full local corrections failed stringent stopping checks. This study
separates arithmetic precision from changes in physical assumptions or fit selection.

## Fixed scope

Reuse all six predetermined diagnostic identities and their original whole stretches.
Each identity receives **fourteen native integration evaluations**, for **84 maximum
overall**, with **zero optimizer starts and no retries**. Four numerical threads
are the total allocation. The old kernels, fits, bounds and result labels stay frozen.

An additional diagnostic kernel uses platform `long double` internally in the same
automatic-derivative equations. The input/output ABI stays float64. The original
float64 packet-clock accumulation and timestamp branch choices are retained; no
sample is dropped, smoothed or interpolated. The actual mantissa width, original
and generated source hashes, compiler flags and binary hash are recorded. A platform
without wider arithmetic cannot run this comparison.

## Evaluations per identity

1. One original and one extended-arithmetic prediction/derivative at the saved center.
2. Both implementations at the same frozen correction with fractions 1, 1/2, 1/4,
   1/8 and 1/16: ten more evaluations.
3. A bounded affine correction calculated from the extended center's residual and
   derivatives, evaluated once with each implementation: two more evaluations.

The affine calculation allows at most 100 linear iterations and does not optimize
the recorded data. No extended endpoint replaces an existing fitted result.

## Measurements and controls

Record central coordinate and derivative differences, actual versus locally
predicted motion/cost, and unchanged stationarity and stability-check quantities.
Comparisons use identical inputs and feasible parameters under each arithmetic
choice; only internal numerical representation changes. Separate wider-arithmetic
corrections from the frozen-direction comparisons.

Known-answer software checks precede archival evaluations: exact straight-disc
motion tests accumulation error and an analytic velocity derivative; finite
differences test every active derivative for all three models and both processing
cases. These controls are numerical checks, not new Earth-model simulations or
statistical calibration campaigns.

The source, input, environment and original-storage hashes are frozen before any
native call. Extraction separately verifies decoded-measurement provenance. Calls
are charged durably before execution, and an exclusive lock prevents duplicate
workers. Interrupted charged identities cannot retry. Completed work cannot resume.

The result can qualify a subsequent numerical proposal or reject a precision
hypothesis. It does not establish a global optimum, weaken stopping tolerances,
change the 30/0/23 findings, or calibrate a scientific decision.
