# Corrected same-realization noise diagnostic

The first six-task study, `data/noisy-realization-attribution-20261110`, is
closed. All six task outcomes are sealed failures with the same `closed study
required` error. No native forecast call was made or charged. Its evaluator
looked for the historical parent under the new study directory, rather than
under the repository root. These failures remain in the original study; none
will be relabeled or retried.

The corrected evaluator resolves the repository root from a study directly
under `data/` and rechecks the same closed parent there. A regression test
reproduced the original wrong path, then passed with the correction. The
complete 16-test oracle suite passed under a new source and environment
binding. The shared task-recovery qualification remains unchanged.

The separate `noisy-realization-attribution-20261111-v2` study completed. It keeps the
original question, six historical noisy streams, models, processing cases,
measurement hashes, known-correction oracle, forecast boundary and scoring.
Its independent allowance remains six native calls, at most 2,592,000,000
packet/query visits, two one-thread workers and a two-hour cooperative
execution ceiling. Technical recovery is separately charged under the
qualified task-recovery policy. No actual aircraft recording or reserved ESA
confirmation group enters this diagnostic.

All six corrected tasks passed technical checks and charged exactly six native
calls. The independent saved-data audit replayed their scores, and the result
was packaged. None meets the existing physical accuracy screen. The
[interpretation](INTERPRETATION.md) explains the surprising outcome. A
[full-length noise-free control](long-noiseless-control/README.md) now passes;
the remaining checks are to align receiver conditioning with the covariance
benchmark, then separate the injected error components.

[Original study plan](PLAN.md) ·
[New software qualification](recovery-v2/qualification/request.json) ·
[Study index](../STUDIES.md).
