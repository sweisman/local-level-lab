# Software qualification of the continuation method

The control suite checks exact/near-boundary answers, repeated starting points,
weak or redundant calibration directions, tight budgets and retained failures.
Analytic controls compare Jacobian-column and unit numerical scaling. Short physical
controls independently generate increments and receiver positions; their validation
uses finite differences rather than the archive's automatic-derivative implementation.
The worker also evaluates actual native tangents and writes epoch results for each
of the three physical models, checking pre-call accounting and the diagnostic reserve.

A deliberately tight, millimetre-whitened finite-difference fixture cannot verify
nanometre-scale prediction stability because of floating-point coordinate resolution.
That case must remain unresolved even when the optimizer reports success. The ordinary
physical solver controls use 0.1 m-scale uncertainties and retain their original
physical-answer tolerances. This modifies software fixtures only; the archive's
GPS covariance is unchanged. Passing small controls is not qualification of global
optima in minute-long recordings.

The report records the test outcome, numerical environment and source/artifact hashes.
These controls make no observed-data fits and confer no Earth-model conclusion.
