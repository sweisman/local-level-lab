# Saved-results review

This is the phase's single permitted failure diagnosis. It reads saved results;
it generates no observations and performs no optimization or native calculations.

The selection is fixed before reading the fit records: the failed seed family's
increment-input, specified-field globe fits, both processing cases and both
starts; the same four settings from the preceding seed family; and the stopped
flat-model start, if returned. This gives at most nine saved records, within the
24-record allowance. No other record can be added after inspection.

The request binds the original completion, exact selected identities, reporting
sources, environment and software checks. One review is charged before reading
the records. Its ceiling is ten minutes, using one numerical thread, with zero
new noise draws, optimizer starts or native calls. It cannot be retried.

The shared `lll.prediction_phase_review` reader uses `lll.studies.closed` to
check input hashes and the existing immutable evidence-snapshot publisher to
preserve its request, selected results, source code and output. It preserves
failed fits and interrupted outcomes separately. It does not change stopping
rules, establish a calibration threshold or reopen validation.

Reproduce the extraction from the frozen request and sources in the evidence
snapshot using `lll.prediction_phase_review.run`. The original charged request
cannot be executed a second time; reproduction must use a separate working copy.

[Phase report](../PREDICTION_PHASE_RESULTS.md) · [Calibration](../prediction-calibration/README.md).
