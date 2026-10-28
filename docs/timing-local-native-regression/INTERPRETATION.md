# Four full-simulator timing checks pass

All four original-start fits pass the complete numerical and raw forecast
screens. Both matched starting-point comparisons agree, and all four original
input, training and error-operator bindings replay byte-for-byte.

The run finishes in 10.7 minutes after 189 source-bound software checks.
It uses 238,386 actual native calls and 126 bounded linear operations, within
its prepaid allowance. No aircraft observations or protected groups are used.

The earlier midpoint-anchor trial remains failed. This separate version checks
both sides using cell midpoints inside the existing ±10-microsecond window.
Every nuisance column and acceptance threshold remains unchanged. The two
originally failed calibration fits are not relabeled: these are newly frozen
regressions from their original starting points and unchanged inputs.

This qualifies four exposed simulator cases, not the whole model/input matrix
or aircraft uncertainty. The next gate is a separately frozen 48-case matrix
covering both input formats, all candidates and both processing settings.
Calibration remains closed. The original 53-stretch findings are unchanged.

[All four results](results.csv) · [Starting-point comparisons](pairs.csv) ·
[Frozen plan](PLAN.md) · [Next analyses](../NEXT_STEPS.md).
