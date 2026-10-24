# Preserve shared rate-sample errors in ESA intervals

The ESA adapter converts rate samples into increments by integrating a straight
line between adjacent samples. Two neighboring intervals therefore share a
measurement at their common endpoint. An independent-increment noise law does
not describe that conversion.

Add a separate, explicitly named rate-point noise law. Declare the covariance
of white errors per rate sample, stationary changing-bias covariance and bias
correlation time for each sensor family. Do not infer point variance from an
IMU name, signal variation or an unspecified bandwidth. These declarations are
not the continuous white-rate PSD used by the incremental-data component.

Retain twelve hidden coordinates: six changing biases and six preceding white
point errors. Initialize the first sample once. At each interval, use the
trapezoidal mean of the two endpoint errors. The new endpoint error drives
both that increment and the next hidden state. Preserve its covariance exactly,
including unequal intervals, all axes and zero/singular components. This is
the logged point-conversion law, not the integral of an unobserved continuous
bias path between samples.

Compare complete generated increment covariances with independent dense
point-error covariances transformed by a trapezoidal integration matrix.
Explicitly test neighboring white-error covariance and distinguish the result
from the continuous-OU integral formula. Use at most sixteen deterministic
cases and twelve intervals per case, one numerical thread and a cooperative
two-minute allowance. No random draws, native calls, fits, original reads or
protected reads are allowed. Freeze a fresh source/environment qualification.

This component alone does not qualify the native trajectory adapter for its
larger error state. That integration, persistent receiver errors, calibration
at bounds and nonlinear prediction coverage remain subsequent gates. The
incremental-data law and all earlier frozen evidence remain unchanged.

[Error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md) ·
[Covariance components](README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
