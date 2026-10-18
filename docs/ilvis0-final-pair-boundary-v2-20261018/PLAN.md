# Corrected saved-context trial for the nearby timing pair

The [earlier trial](../ilvis0-final-pair-boundary-20261018/RESULTS.md) completed
both fresh controls in six native calls. Both target identities stopped before
native evaluation: their newly attached GPS context contained receiver dictionaries
instead of the numerical latitude/longitude/height rows used by extraction.
The trial is complete and its failed starts remain charged. Never restart it.

The correction builds the context from the sealed original endpoint arrays,
saved relative receiver epochs and preselected receiver records. It reproduces
the extraction convention exactly: latitude and longitude in radians, height in
metres, and relative time equal to receiver UTC time minus the frozen first IMU
interval start. Validate this equality before reading originals. No measurement,
epoch, physical model, bound, native kernel or stopping tolerance changes.

`lll.ilvis0_saved_context` provides the checked conversion. The v2 worker privately
reuses the frozen executor and overrides context construction only. Old source
files, prepared artifacts, failures and allowances remain untouched. Each v2
identity has a new suffix and a separately frozen source/input/environment set.

## Finite limits

Two fresh smooth controls at three calls each and the original
`370cec66878c4c1cf84b4ceb` profiled-removal specified-field-globe primary/repeat
at 26 calls each: **four identities, 58 native calls, zero optimizer starts**.
Maximum 402,048 clock queries, six bounded affine solves, four total numerical
threads, no retries. No other stretch or model is included.

Qualification is one 33-test batch with a 120-second ceiling: the existing 21
candidate controls, nine saved-context checks and three v2 worker checks.
At most 1,024 software callbacks, 81 compiled-motion calls and six compiled clock
comparisons. Tests may read sealed metadata and endpoint arrays, never originals.
The real-source regression verifies all 554 receiver epochs for each target.

Require both controls before target evaluation, unchanged source reproduction,
full two-sided gates, source-to-final movement limits and primary/repeat agreement
(relative cost 10^-6, per-axis prediction RMS 0.01 m). Record calls before execution;
an incomplete transaction blocks resume. Completed or charged identities may not
restart. Preserve finite limits even if a task fails before using its allowance.

Publication performs no native calls. A successful result still needs the complete
saved companion/model review before changing the current **51 globe / 0 flat /
2 unresolved** findings. The other stretch remains outside this trial.
