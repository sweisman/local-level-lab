# Saved prediction errors: scope and safeguards

## Question

How do the saved errors grow after training, and what temporal and cross-axis
structure do they contain? Do the two working error cases leave materially
different patterns that should be examined before broader prediction tests?

This is a descriptive error-model assessment. It does not estimate raw GPS or
gyro noise separately, calibrate confidence, change a fit or select a model.
Prediction errors combine receiver, IMU, calibration and physical-model effects.

## Inputs

Use the verified, closed wider-precision ESA development comparison. Preserve
its source and input hashes, all 24 outcomes, the 22 completed error curves,
the 800/400 training/prediction boundary and its training-only primary choices.
The two deadline-limited starts remain unavailable. Analyze all completed
starts; show selected primaries separately rather than counting starts as
independent observations.

No original aircraft file, new position observation or protected confirmation
group is an input. No IMU propagation, parameter search, refit or new forecast
is permitted. Source records and numerical/accuracy labels remain unchanged.

## Calculation

Use shared residual-distribution and autocorrelation helpers. Report each
physical axis separately in training and prediction: mean, RMS, centred spread,
absolute quantiles, cross-axis covariance/correlation, and epoch-lag correlation
at 1, 5, 10, 30 and 60 samples with the actual lag times.

Also describe first differences divided by their actual time intervals. For
uniformly sampled sections, report centred Fourier variance in periods longer
than 60 seconds, 10–60 seconds and shorter than 10 seconds. If cadence is not
uniform, flag the spectral calculation as unsupported; do not interpolate or
drop measurements. Constant channels have undefined correlations, not invented
zeros. These statistics do not establish stationarity or independent sample counts.

Reuse fixed sixty-second error blocks without crossing the training boundary.
Report the saved weighted training RMS as a descriptive fitted statistic, not
a chi-squared test or a complete prediction-uncertainty estimate. Plots use the
original saved errors; no trend is removed from a prediction or score.

## Qualification

Before execution, test independent constructed constant, ramp, alternating and
sinusoidal series, known cross-axis relationships and Parseval variance.
Check irregular timing, invalid/nonfinite input, unchanged arrays and the
absence of influence from later errors on training summaries. Test preservation
of missing predictions and primary selections in the study/report interfaces.

Bind the complete source list and environment before the qualification report
is produced. Freeze the closed parent report and exact curve artifacts before
the diagnostic starts. Reuse the shared study lifecycle and append-only work
journal, without copying a worker or numerical library tree.

## Separate finite allowance

One diagnostic start, one numerical thread, at most 24 saved curves and 28,800
saved error epochs; each curve is capped at 1,200 epochs with 800 training rows.
There are at most 24 section-pair summaries and five declared correlation lags.
Each complete curve has two position-error sections and two first-difference
sections, each with three axis spectra. The cooperative ceiling is five
minutes. Native integration calls, optimizer starts, new propagations and
original/protected reads are all zero. There are no retries.

Charge saved-curve and epoch processing before the calculation. Record actual
work and preserve failures. Audit and package the saved statistics without any
fit or propagation. No remaining allowance from the observed run is reused.

## Interpretation

Fitted training errors and their correlations are not independent validation.
Later positions were excluded from fitting, but this recording has informed
method development. Estimated correlations and ranges are descriptive, not
calibrated coverage or a total receiver/IMU noise law. Do not alter an error
policy merely to favour a physical candidate.

Results guide the next error-law qualification and broader predictive tests.
The 53-stretch findings and seven protected ESA groups remain unchanged.

[Verified parent](../esa-observed-wide-pilot/INTERPRETATION.md) ·
[Error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
