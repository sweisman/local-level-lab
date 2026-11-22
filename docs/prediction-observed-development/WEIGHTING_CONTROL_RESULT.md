# The ESA prediction gap comes from the added IMU-error weighting

One 20-minute ESA development recording has now been fitted three ways on
**the same 800 early GPS positions**. Each fit then propagated an uncorrected
IMU trajectory to the same 400 later GPS times without using those later
positions to adjust it. The recorded
IMU increments, clock, physical model, calibration bounds and starting point
were held fixed.

| Fit | Early horizontal error | Later horizontal error | Evaluations |
|---|---:|---:|---:|
| Earlier receiver-only weighting | 0.057 m | 7.803 m | 25 |
| New receiver-only control in current code | 0.057 m | 7.803 m | 25 |
| Current added IMU-error weighting | 39.961 m | 249.411 m | 9 |

The new receiver-only control reproduced **every fitted parameter and every
saved forecast coordinate exactly** from the earlier accurate fit. The
current code therefore still reproduces that fit on these measurements. In
the matched current-code comparison, introducing the declared IMU-error
covariance changes the optimum and greatly worsens the uncorrected trajectory's
position accuracy.
The newer covariance was taken from generated development controls; its noise
levels were not measured for this ESA instrument. The comparison isolates that
modeling choice as the operative difference in this recording. It does not
establish the instrument's true error law.

Both receiver-only fits pass the preset physical-accuracy screen on the early
and later sections: later horizontal RMS is below 10 m and later vertical RMS
is 13.373 m, below its 30 m limit. The added-IMU-error fit fails the horizontal
screen in both sections, though its later vertical RMS is 4.351 m. These are
accuracy checks on the saved uncorrected trajectories from one development
recording, **not** calibrated confidence
limits or an Earth-model decision. All fits passed their numerical stopping
checks. The seven other ESA flight groups remain reserved.

The [completed fixed-parameter check](ERROR_LAW_CROSS_SCORE_RESULT.md) scored both
saved fits under both training objectives without another optimization. The
added IMU-error law prefers its own saved fit over the more accurate raw
trajectory's parameters. After that,
the observation-error model must be established from recorded instrument and
receiver behavior and qualified on generated and development controls before
using the reserved groups. The
receiver-only fit is an accurate development forecast under its assumptions;
it cannot by itself supply calibrated uncertainty or validate an Earth model.

The weighted model also defines a different prediction: a later position
conditioned on the receiver errors already observed in training. That
conditional forecast was **not calculated in this control**. A [separate
source-frozen check](CONDITIONAL_FORECAST_RESULT.md) has since scored it at
2.85 m later horizontal RMS on the same development recording. The 249.411 m
figure describes the saved uncorrected IMU trajectory.

The [machine-readable comparison](weighting-control-result.json) verifies the
three sealed fit and forecast artifacts, exact input hashes, original training
split and unchanged later scoring rows. The [frozen control plan](WEIGHTING_CONTROL_PLAN.md)
records its one start, 200-evaluation cap and four-hour cooperative limit. The
control completed in 2,797 seconds; 30 adjacent receiver-window tests and the
six focused weighting-control tests pass. No confirmation group was opened.
