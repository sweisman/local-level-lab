# Paired aircraft error-law pilot

**12 generated recordings and 24 candidate fits were verified.**
Each recording was fitted under both fixed IMU error laws using the
same gyroscope, accelerometer and earlier receiver measurements.
The complete comparison was saved before later positions were scored.

Numerical checks passed for 24/24 fits; 24/24 also passed the declared physical prediction screen. Training scores could be ranked in 12/12 recordings. The numerical minimum matched the generating error law in 6 of those ranked cases. The largest training-score separation was only 8.20195e-05 negative-log-likelihood units. The largest fixed-parameter future scale ratio was 1.00000223.

Comparison status by recording: active bounds unsupported: 12.

These rankings are **not a calibrated error-law selection**. Every
scientific decision remains **abstain**. The reported 95% marginal
counts use fixed calibration parameters and omit uncertainty caused
by fitting calibration, especially at active bounds. They are
descriptive diagnostics, not demonstrated 95% coverage.

- Physical position: 1924/2880 fixed-parameter marginal intervals contain the generated value.
- Future receiver report: 2242/2880 fixed-parameter marginal intervals contain the generated value.

The two-minute records use one predeclared noise seed and
separately fitted physical candidates. The study tests error-law
comparison and prediction mechanics, not Earth-model selection,
aircraft error coverage or statistical significance. No recorded
aircraft data or reserved confirmation groups were read.

[Finite plan](PLAN.md) · [Per-fit results](results.csv) · [Sampling comparison](SAMPLING.md) · [Next analyses](../PREDICTION_ERROR_LAW_PLAN.md).
