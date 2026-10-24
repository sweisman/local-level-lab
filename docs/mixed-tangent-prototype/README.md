# Testing a faster calculation

**All nine small checks pass:** three source-transformation checks and six
compiled cases. They used one released numerical core. The running noisy-data
study is unchanged.

The proposed optimization keeps the wider-precision position calculation and
uses ordinary precision for the slopes that guide the optimizer. Predicted
positions and residuals must stay bitwise identical in the first checks, and
all 26/27 derivative columns must meet the fixed comparison tolerance.

This is an isolated software prototype. No speed improvement or long-record
accuracy is established yet. The next gate is a separately frozen long-record
benchmark, followed by training and prediction qualification.
It does not authorize an observed fit or alter a scientific result.

[Verified test evidence](qualification/README.md) ·
[Test scope and limits](PLAN.md) · [Reproducibility](../REPRODUCIBILITY.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).

The [completed long-record benchmark](../mixed-tangent-long-controls/README.md) preserves positions and residuals exactly but fails the derivative tolerance on all six cases. Its speed improvement does not qualify a replacement for fitting.
