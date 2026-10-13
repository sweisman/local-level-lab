# Portable control-test repair

The rectangular solver's control test currently requires the older TRF method to fail
one ill-conditioned problem. The saved local screen did fail that check, but GitHub's
run of the same control succeeded. A particular competing method's failure is not a
portable correctness requirement.

`ci-test-repair.patch` removes that negative assertion and retains the rectangular
method's known-answer, accuracy, fresh stability, stationarity and evaluation-budget
checks. It adds an explicit objective check. No solver thresholds change.

The repair was applied after verified trial completion and publication. The original
test remains preserved in both source snapshots, matching the completed manifest.
The targeted rectangular and recovery-screen suites passed all 26 tests. The patch
records the change for reproduction against the original source:

```sh
patch -p1 --input=docs/ilvis0-rectangular-recovery-trial-20261012/ci-test-repair.patch
```

The targeted tests use the pinned Python environment and at most two numerical threads.
Preserve the completed trial's source
snapshot and original 29/30 versus 30/30 screen results; do not regenerate them to match CI.
