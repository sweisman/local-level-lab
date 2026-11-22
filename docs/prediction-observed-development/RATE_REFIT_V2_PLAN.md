# ESA rate refit: corrected software qualification

The first six-task generated smoke study is sealed as a terminal software-gate
failure. Its two original reference fits were themselves nonconverged at the
eight-evaluation smoke ceiling. The new fits reproduced the saved linear-point
results, but the first gate incorrectly demanded numerical convergence from
these deliberately short generated controls.

This separate study keeps the same six methods, input sources, training-only
fit procedure, physical model, nuisance bounds and finite per-task limits.
Generated qualification now checks that the pipeline reproduces the original
fit status and linear-point fit/forecast. It does not call a nonconverged
generated fit a scientific success. Observed development fits must still
converge and reproduce the original linear-point baselines to pass.

The original first smoke artifacts and charges remain unchanged. A fresh
identity, source/environment binding and generated six-task smoke are required
before observed preparation. At most one start per task is allowed initially;
unfinished tasks can use the same separately charged technical recovery rule
as the first plan. No completed numerical failure is retried. The observed
allowance remains three workers with one thread each, at most 700,000 native
calls and 45 billion packet/query visits per task, and four hours overall.
The seven reserved ESA groups remain unopened. Results are development
prediction diagnostics, not an Earth-model or calibrated detection claim.
