# Prediction errors move together

**The saved-error check is complete.** It examines all 22 available forecasts
from the ESA development comparison, preserving the two deadline failures.
No measurements, fits, predictions or model rankings change.

The preferred model's nearby prediction errors are strongly related: lag-one
correlations are about **0.991–0.992** on the north, east and height axes.
Even the changes between successive errors remain correlated, about
**0.974–0.981**. Errors therefore evolve smoothly rather than behaving like
independent draws at each receiver epoch.

This matters for uncertainty. Four hundred later positions are not four hundred
independent tests. Correlated errors can arise from accumulated inertial error,
calibration, receiver error or shortcomings in the motion model. This check
does not separate those causes or measure the receiver's noise by itself.

The preferred model's weighted training RMS is about **0.533** under the
short-memory working assumption and **0.0675** under the persistent-error
assumption. Those numbers describe different fitted objectives. A smaller value
does not establish that one error assumption is correct.

## What was preserved

The check keeps training and later prediction separate, and retains alternate
starts without counting them as extra flights. It reports distributions,
cross-axis covariance, five correlation lags and fixed sixty-second blocks.
The selected forecasts are plotted without removing their trends.

The original query spacing varies from about **0.999002 to 1.000003 seconds**.
Under the frozen uniform-sampling requirement, all 264 axis/section spectral
checks are flagged unsupported. No observations are interpolated to make a
Fourier plot. Correlations and error changes use the actual saved times.

All **25 software tests** passed before the calculation. It processed 26,400
saved error epochs in **3.15 seconds**, with zero fits, IMU propagations or
original-data reads. The publication's 88 artifact hashes are verified.

## Next

Check an error model that includes both receiver and accumulated IMU errors,
using generated data with known correlated errors before broader observed
prediction tests. Keep all candidates under matched assumptions; do not tune an
error allowance to make a preferred candidate pass. Statistical confidence
remains uncalibrated. Seven ESA confirmation groups remain protected.

[Full statistics and plot](README.md) · [Axis statistics CSV](axis-statistics.csv) ·
[Frozen scope](PLAN.md) · [Parent comparison](../esa-observed-wide-pilot/INTERPRETATION.md) ·
[Next analyses](../NEXT_STEPS.md).
