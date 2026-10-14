# Paired qualification of wider-arithmetic fits

**Completed and qualified: all 16 fits passed in 129 native sweeps.** Both targets
now favor globe geometry under both processing assumptions, with passing controls
and perturbed repeats. The combined findings are **32 globe preferences, zero flat
and 21 unresolved stretches**. [Fit results](RESULTS.md) preserve the evidence.

The [completed precision comparison](../ilvis0-shared-leg-precision-20261014/RESULTS.md)
found that wider arithmetic passes unchanged stopping probes at the two cost-only
failures. The completed trial confirms that improvement across full model comparisons
and repeated starts on the same recordings.

The targets are the IMU8 recording on 24 October 2009 and the DMS recording on
7 October 2015. Each has a completed recorder on an overlapping flight leg. Every
target receives all three models under both processing assumptions. Their original
whole stretches, measured increments, receiver positions, calibration bounds and
numerical tolerances remain fixed. Different recorders retain separate calibration.

The [finite plan](PLAN.md) permits **16 starts and 992 native integration sweeps
maximum**, with no retries and four total numerical threads. Twelve primary fits
and two controls allow forty fitting evaluations each; two perturbed repeats allow
two hundred each. Each start also permits two diagnostic predictions. The measured
ceiling is approximately **7–9 hours**, with earlier completion possible.

Both matched controls must pass. Each target needs all six primary fits and its
repeat to converge and agree before its numerical preference can be reported.
Failed attempts stay recorded; a repeat cannot replace a primary. The September
disc endpoint's separate vertical-stability problem is outside this cost-only trial.

Starts and native calls are journaled before execution, results are hashed and
written atomically, and an exclusive lock prevents duplicate workers. The detached
worker packages the completed evidence automatically. The trial does not establish
statistical significance, a global optimum or the background field's physical cause.
