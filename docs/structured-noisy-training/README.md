# Can noisy measurements predict the later track?

**The two-minute study is running.** Its 24 generated cases test the complete
calibration and prediction procedure with known measurement errors. There are
no new aircraft results yet.

The software receives noisy gyroscope and accelerometer readings, plus earlier
receiver positions. It fits calibration using those earlier observations, then
predicts the remaining track. Later truth is kept out of fitting and error
correction.

Each case has 79 earlier positions and 40 later checks. The matrix covers all
three generating models, both processing assumptions and both recorded-increment
and sampled-rate error formats. Two starting points test repeatability. Four
workers each use one numerical thread, within a fixed two-hour allowance.

The report will distinguish numerical completion, raw prediction accuracy,
error-conditioned prediction accuracy and calibration uncertainty. Short
two-second examples already check the connected software, but cannot identify
calibration from their six earlier positions. This longer test addresses that
limitation without changing the physical error limits.

Each candidate predicts its own generated motion. These cases do not add votes
to the 53-stretch globe/flat comparison. Passing them would qualify the tested
prediction procedure under its supplied error assumptions; actual archive noise
and statistical confidence remain separate questions.

[Frozen study plan](PLAN.md) ·
[Shared software qualification](../integrated-noise-covariance/shared-native-protocol-qualification/README.md) ·
[Preserved initial launch](initial-launch/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
