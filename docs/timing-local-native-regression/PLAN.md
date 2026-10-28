# Check local timing verification in the full simulator

The [local mathematical qualification](timing-local-qualification/INTERPRETATION.md)
passes all 36 fits, eight direct controls and nine starting-point comparisons.
It replaces distant timing-cell midpoints with midpoints inside the existing
±10-microsecond neighborhood. The earlier four-fit trial remains failed.

## Frozen question and inputs

Run the same four exposed generated-data cases from their original declared
starts, not their saved fitted answers. Use seeds 281474977010692 and
281474977010693, the point-error law, specified-field globe and the original
profile setting, with starts zero and one. Preserve the two originally passing
controls and two originally failed labels. Require byte-identical original
input, training and error-operator bindings.

Only the qualified local timing verification changes. Preserve all 27 nuisance
columns, physical bounds, mean/noise model, packet clock, near-zero rule and
forecast screens. Keep numerical limits: relative cost 10⁻⁸, stationarity
10⁻⁴, position-change RMS 1 mm and maximum 1 cm. Actual fresh evaluations must
verify every retained timing cell; no cell is dropped after seeing its result.

## Separate finite allowance

This is a new four-fit allowance, not a retry or extension of the closed trial.
Freeze source, environment, selection, inputs and budgets before launching.
Use four workers with one numerical thread each, at most 200 residual/Jacobian
evaluations per fit including final checks, 620 bounded linear operations per
fit, two native builds per worker and a one-hour cooperative ceiling. No retries.
The unchanged shared accounting formula caps native calls at 239,816 and packet
visits at 1,506,051,012. Interrupted starts remain charged; unused work closes.

Reuse the shared definition, evaluator and reporter; do not copy worker trees.
First pass source-bound software tests. Independently audit saved traces,
charges, original bindings and both starting-point comparisons after execution.
Publish every failure without refitting during packaging.

## Decision

All four fits, raw forecast screens, original binding replays and both paired
start checks must pass before preparing a separately frozen 48-case optimizer
qualification. A failure blocks that dependency and is preserved for diagnosis.
Neither result reopens calibration automatically. Protected aircraft groups and
the original 53-stretch findings remain untouched.

[Previous failed trial](timing-optimizer-regression/INTERPRETATION.md) ·
[Next analyses](NEXT_STEPS.md).
