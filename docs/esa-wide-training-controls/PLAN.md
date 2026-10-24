# Qualify wider-precision training and prediction

## Status and dependency

Planned only. Do not prepare or launch this study until the 48 long known-motion
controls qualify and the training adapter passes its own source-bound checks.
The definition, shared protocol binding and saved-result reporter currently pass
16 metadata checks. Four native independence/accounting checks are prepared;
they wait for numerical capacity and are not reported as passed.
The present motion controls supply true calibration. This study must instead
estimate calibration from earlier positions, then predict unused positions.

## Matched protocol

Reuse the qualified twenty-minute training protocol and its generated inputs:
all three candidates, both processing cases, both working receiver-error cases
and two declared starts, for **24 identities**. Preserve the turning/climbing
trajectory, complete calibration bounds, earlier-only initialization and gravity
anchor, 800 training epochs and 400 later scoring epochs. True calibration and
initial state must not be supplied to the estimator.

Use the shared protocol-binding interface to replace only the problem factory
with the qualified wider-precision factory. Reuse the same fitting and stopping
code, starting points, maximum evaluations, forecast order and physical scoring.
Bind both original protocol hashes, the replacement provider, and each one-import
transformation. No process-global function is patched and no worker is copied.

The training residual and its complete 26/27-column Jacobian must use coordinate
differences formed before conversion to binary64. Forecasting must use the same
wider tangent, continue without receiver resets, and accept no later positions
or covariance. Keep original binary64 packet scheduling, query fractions,
parameter products and processing-fraction mapping. A change to those conventions
would require a separate method and qualification.

## Qualification and fixed limits

Before preparation, test original-function isolation, exact source binding,
complete nuisance columns, real native call accounting, unchanged fit allowances
and absence of later-position influence. Change later generated positions only
after the forecast is saved and confirm that training and forecasts remain
identical. Require the actual standalone worker loader to pass.

Preserve the original per-section targets: horizontal and height RMS at most
0.1 m and maximum spatial error at most 0.5 m. Require the original numerical
stopping checks; repetitions remain sensitivity tests, not confidence intervals.

Freeze a new allowance of **24 identities, at most 4,824 native calls and
931,411,200,000 packet/query work units**, four single-thread workers and a
cooperative **eight-hour ceiling**. Each identity allows at most 200 fitting
evaluations plus one forecast, with no retries or allowance transfers.
Construction journals separately bound each identity to 360,000 intervals and
362,001 generated samples. Charge operations before execution and preserve all
failures. No original aircraft file, observed fitting start or protected flight
is authorized by this study.

Publish from sealed results without refitting or regenerating data. All 24 cases
must pass before a separately frozen observed solver revision can use this
method. The NASA baseline, original ESA fit labels and seven reserved confirmation
groups remain unchanged.

[Known-motion gate](../esa-wide-tangent-controls/README.md) ·
[Prediction protocol](../PREDICTION_VALIDATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
