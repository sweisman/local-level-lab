# What the motion diagnostic establishes

All eleven frozen identities passed: 24 analytic paths, 2,304 generated-noise
realizations and 2,048 fixed receiver-window centers. No gyroscope values or
Earth-model outcomes were used. The original zero-eligible inventory is unchanged.

## Adjacent differences are noise-sensitive

In generated straight flight with independent velocity noise of 0.05 m/s,
the old adjacent-difference statistic flags all 128 straight controls for turning.
The ten-second trend flags none. At 0.2 m/s noise, the trend can still give false
flags and miss turns, especially with correlated errors. Its smoother appearance
does not remove the need for an error assessment.

Intervals using the supplied Gaussian correlation and conservative intervals
allowing arbitrary temporal correlation cover the noise-free trend in all
256 realizations of every declared family. Each exact one-sided 99% coverage
lower bound exceeds the frozen 0.95 requirement. This is software qualification
under supplied marginal variances, not measured aircraft uncertainty.

## The real recording does not support a simple threshold replacement

Of 2,048 fixed centers, two lack complete receiver windows and 1,507 windows
meet airborne speed and IMU-time support. Among these:

- Adjacent differences flag 920 windows for turning; the trend estimate flags 749.
- Median absolute vertical speed exceeds 1 m/s in 201 windows.
- No trend uncertainty interval lies wholly inside ±0.02°/s, even assuming
  independent errors with the receiver's reported velocity covariance.
- Allowing arbitrary temporal correlation also confirms no quiet windows.
  Most windows are ambiguous under either uncertainty calculation.

The reported covariance has not been observationally calibrated. These wide
intervals do not establish that the aircraft was continually maneuvering.
Conversely, a trend estimate below the cutoff does not demonstrate quiet flight.
The diagnostic targets a window-average velocity trend; nonlinear aircraft
motion can differ from its instantaneous course derivative.

## Consequence for the roadmap

A new selection policy cannot be justified by replacing adjacent differences
with smoother point estimates alone. Receiver-error assessment and motion-model
adequacy remain needed before any revised inventory. The current inventory,
controls, unsupported cases and thresholds stay frozen. Protected confirmation
recordings remain untouched. Meanwhile, the higher-priority native prediction
uncertainty and training-only adapter work can proceed independently.

[Results and every window](README.md) · [Frozen plan](PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
