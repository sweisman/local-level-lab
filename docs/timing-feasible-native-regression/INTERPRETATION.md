# All six native regressions pass

**All six fits, three starting-point comparisons and six original-input replays
pass the independent audit.** The run finishes in 10.6 minutes using four
workers with one numerical thread each. Every fit passes all nine timing-cell
checks under the original numerical and position-error limits.

The cases include an earlier successful control, an earlier numerical failure
and the latest calibration failure, each with its two prescribed starts. The
first two retain all 27 nuisance parameters; the last retains all 26. Every
input, training observation and error-operator binding matches its original.
No earlier result is relabeled.

For the latest formerly failing case, the corrected verification accepts the
fit at the same fitted cost and prediction errors: about 0.70 m horizontally
and 1.60 m vertically. This checks the numerical correction without changing
the simulated measurements or scientific acceptance thresholds.

The six fits use 220 evaluations and 154 linear operations. Actual native work
is 357,544 calls and 435,412,458 packet visits; the larger prepayments remain
charged. There are no retries. The execution passed 338 source-bound software
checks before freezing. A read-only auditor metadata repair subsequently passes
339 checks. Its source, regression test and binding record are included in the
publication receipt; no fit was rerun for that repair.

These are exposed generated-data regressions, not new aircraft observations or
independent statistical validation. The next gate is a fresh 48-case native
matrix covering all three generating candidates, both input formats and both
processing settings. Calibration remains closed without a usable threshold,
and the 53-stretch aircraft findings are unchanged.

[Verified report](README.md) · [All fits](results.csv) ·
[Starting-point comparisons](pairs.csv) · [Frozen plan](PLAN.md) ·
[Next analyses](../NEXT_STEPS.md).
