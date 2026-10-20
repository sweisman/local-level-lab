# Finite structured-error benchmark

Freeze and run three software identities sequentially on one worker/four threads:

1. Dense equivalence at 16 epochs with 27 residual/Jacobian columns; verify
   whitening, inverse, determinant and subset projection against dense references.
2. Structured setup at 4,000 epochs with one column, followed by whole whitening,
   block whitening and block inverse checks.
3. The same operations at 64,080 epochs with 27 columns, matching the inspected
   ESA receiver timeline's observation count without reading that dataset.

Use fixed generated irregular timestamps, a declared white + two exponential +
offset/drift covariance, and deterministic sinusoidal values. Do not estimate
covariance, run native integration, read archival measurements or fit parameters.
Require the dense gate before benchmarks. The 20 focused unit checks have passed;
preserve their source and the relevant covariance implementation in the freeze.

Ceiling: three identities, three filter setups plus one small projection setup,
one whole whitening, one block-whitening and one block-inverse pass per benchmark,
64,080 epochs/27 columns maximum, 300 seconds overall, no retries. An interrupted
charged identity is not rerun; completed or terminal studies never restart.

Report actual setup/apply times, cached array storage, process peak resident memory,
inverse/block discrepancies and deterministic output hashes. Verify linear cache
growth between the two sizes. Dense arrays are permitted only for the 16-epoch
reference; no whole-record covariance, factor or projection matrix is permitted
in the long paths.

This qualifies supplied-covariance operations, not covariance estimation,
bounded nuisance uncertainty, observational coverage, an ESA input adapter or
native streaming integration. Those roadmap requirements remain separate.
