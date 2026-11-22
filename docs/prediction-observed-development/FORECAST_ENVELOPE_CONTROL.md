# A forecast range must also distinguish candidates

The [software control](../../analysis/lll/forecast_envelope_contrast.py)
checks two or three precomputed forecast ranges against a withheld path.
It reports a **descriptive unique candidate** only if exactly one range
contains every withheld coordinate. If ranges are broad enough that two
models both contain the path, it abstains. It also rejects a comparison
between true-position and receiver-measurement ranges or a range that only
claims marginal, rather than whole-path, coverage.

Six deterministic tests pass, including a correct narrow range, a very broad
competing range, all three candidate names and mismatched targets. This is a
method check, **not a model result**. No aircraft data or new physical fits
were used. Nominal generated ranges are not calibrated for aircraft; the
control always reports `scientific_decision: abstain`.

The next step is a separately frozen generated fit that saves **both**
true-position and receiver-measurement ranges before opening later data,
then checks coverage, usefulness and nonlinear calibration effects across
distinct routes and fresh noise draws.

[Qualification plan](NOISE_AWARE_ADEQUACY_PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md)
