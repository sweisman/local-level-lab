# Training-only error-law software check

Twelve focused tests pass against six source files and the recorded Python,
NumPy, SciPy and pytest versions. The [binding](request.json),
[test report](tests.xml), [verification receipt](verified-checks.json) and
six hash-matched source copies under `source-freeze/` preserve exactly what
was checked.

The software can compare declared error laws using only earlier observations.
It can remove a fitted linear mean from that comparison and withhold a finite
forecast when a calibration direction cannot be learned from training.
An independent dense calculation checks the shared-error arithmetic.

A known-answer example shows the limit: white and persistent errors can have
the same one-epoch training distribution while implying very different later
uncertainty. This is a software control. It does not estimate the aircraft's
error law, test a nonlinear fit or establish prediction coverage.

The [next gate](../PREDICTION_ERROR_LAW_PLAN.md) is a finite known-answer
study with uncertainty learned from earlier data, followed by an observed
development check. Protected ESA confirmation recordings remain unopened.
