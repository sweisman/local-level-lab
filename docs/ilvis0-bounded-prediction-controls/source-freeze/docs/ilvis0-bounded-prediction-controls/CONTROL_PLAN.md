# Finite uncertainty qualification

Freeze eight software identities, sequentially, on one worker/four threads:

1. A small structured-versus-dense conditional forecast gate.
2. Six coverage controls, each with exactly 512 generated error realizations:
   fixed linear mean; true parameters at bounds; 27 parameters with unidentified
   and weak directions; bounded nonlinear mean error; an adaptively learned
   design; and a two-member covariance union with shared calibration source.
3. A structured forecast at 42,720 training and 21,360 future epochs with 27
   columns, without dense long-record covariance matrices.

The coverage controls use separate fixed design, calibration-noise and joint
training/future-noise streams. Correlated three-axis errors come from the
declared Gaussian family. Ground-truth parameters, calibration data, training
data and future data are preserved. Future observations are supplied only to
the coverage evaluator after each envelope is produced.

Use total failure allowance 0.05: 0.01 for shared scale where estimated, 0.02
for nuisance uncertainty and 0.02 for future noise. Known-scale controls spend
zero scale allowance. A candidate design learned from the tested observations
uses the full training-noise dimension; it cannot use fixed-rank calibration.
Every original parameter column remains present. Unsupported outputs count as
misses, not omitted samples.

For each coverage control, report simultaneous whole-future coverage, unsupported
count and the exact one-sided 99% binomial lower bound. Require that lower bound
to reach 0.95 for software qualification. This deliberately conservative screen
is separate from both the analytic assumed-model bound and future observational
calibration. Preserve a failed screen without rerunning or changing its seeds.

The nonlinear control's remainder is an independently declared bounded function
over its complete parameter box. The archive's saved axis probes do not supply
such a global guarantee. No native/observed-data prediction is authorized by a
software pass alone.

Limits: eight charged identities, 3,072 coverage realizations, at most two
covariance alternatives per control, at most 40 epochs in dense references,
64,080 total epochs/27 columns in the long structured path, 300 seconds overall,
zero original reads/optimizer starts/native integrations, no retries. The dense
gate precedes coverage; native work remains blocked unless every required
qualification passes. Check the wall allowance cooperatively between bounded
operations and realizations. Once exhausted, record a terminal result and start
nothing further. Do not signal or terminate a process; an operation already in
progress finishes before the allowance is checked again. Record any overrun.

The long check reports runtime, linear cache storage, process peak memory and
the identity that conditional variance plus squared training-response norm
equals the supplied unconditional marginal variance. This is an independent
long-scale check without constructing a dense matrix.

Keep source/input/environment hashes, immutable charges/results, generated data,
failures and complete publication. Completed or terminal studies cannot restart.
