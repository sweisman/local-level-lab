# Next gate: noisy calibration and later-position prediction

The fixed-error adapter, rate-sample error generator and efficient work
accounting are software-qualified. The connected short protocol also passes
its software checks. The completed two-minute generated study predicts later
positions within the physical limits in all 24 cases, but only 20 pass the
numerical stopping checks and all 24 reach calibration bounds. Those results
do not qualify prediction uncertainty. The earlier twenty-minute noisy study
remains an accuracy failure. A separate
[bounded-prediction component](../ilvis0-bounded-prediction-controls/README.md)
and its [structured adapter](bounded-state-qualification/README.md) already
pass generated software controls, including boundary cases. The
remaining gate is to supply justified global nonlinear remainder bounds and a
validated aircraft error law to that component, then test the complete
estimator over longer noisy records. Component checks alone cannot establish
withheld-prediction accuracy or calibrated uncertainty.

A saved-only inspection of the closed twenty-minute noise study finds
`gyro_gain_y` at its −1% lower bound and `time_offset` at its +10 ms upper
bound in all 24 fits; `gravity_delta` reaches its lower bound in 18. The
generator planted `gyro_gain_y` at ±0.15% and timing offset at ±0.7 ms,
switching signs between processing cases. Both planted values are inside the
fit bounds. The matched settings share one noise seed, so these counts are a
diagnostic pattern, not 24 independent replications. Before changing a fit or
error law, test why the fitted limits diverge from the known planted values
and quantify their coupled effect on the missed horizontal accuracy screen.
Do not widen bounds to make the existing failures pass.

The existing saved-fit boundary diagnostic also finds an outward local descent
direction at the active Y-gain and timing limits in **24/24** fits, and at the
gravity lower limit in **18/18** fits that reach it. Thus these two ubiquitous
bound hits are not explained merely by an optimizer stopping with an inward
descent direction. A local gradient does not establish a global optimum or
distinguish weak parameter identification from a mismatch in timing, motion or
the declared error process. This check reads the closed fit artifacts and
their frozen calibration reference; it performs no refits or new draws.

The [source-bound known-calibration benchmark](../noisy-prediction-benchmark/README.md)
already gives a stronger scale check: a **33.77 m** horizontal error scale
for the declared 20-minute noise law, even with known starting
state, calibration and nominal trajectory. That exceeds the failed study's
10 m horizontal accuracy screen before fitting uncertainty is added. It is
an expected error scale under assumed noise, not observed-aircraft coverage
or a new acceptance rule. Preserve the original failed screen. Any replacement
accuracy and uncertainty criteria belong in a separately frozen study fixed
before its outcomes are inspected.
The [matched realization diagnostic](../noisy-realization-attribution/PLAN.md)
is the next bounded check of whether this particular noise draw or fitted
calibration accounts for the larger observed misses.

## Match the generated input to its error model

Keep recorded-increment errors and rate-point errors separate. The earlier
failed noisy study generated continuous white noise and integrated changing
bias directly into increments. Preserve that study and its results.

For rate samples converted by the trapezoidal rule, generate noise at the sample
points first. Neighboring intervals share an endpoint. Sampled changing bias
must also be integrated by that same rule; it is different from an exact
continuous-time bias integral. The completed generator checks compare against
closed-form sample covariance and prefix-reproducibility controls.
Point variance is an explicitly supplied squared-rate quantity, not a hardware
specification or an automatic conversion from continuous white-noise PSD.

Reserve all generated random variates before drawing. Use separate named
streams for each sensor, white noise and changing bias. Extending the later
record must preserve the earlier generated inputs exactly. The
[qualified rate-point generator](rate-point-input-qualification/README.md)
now checks this law; preserve that result rather than rerunning it.

## Qualify the complete prediction path

The [short native protocol](short-native-protocol-qualification/README.md)
checks all 26/27 calibration columns, each physical candidate, both processing
assumptions and both input laws. The
[two-minute study](../structured-noisy-training/README.md) fits only earlier
noisy measurements and freezes covariance at its declared midpoint anchor.
Future studies must preserve Gaussian normalization and keep raw forecasts
separate from
earlier-error-conditioned forecasts. Score later physical truth only after
both forecasts and their calibration binding have been saved.

Distinguish prediction targets explicitly. A future receiver measurement includes
receiver white noise, persistent offsets and drift; a noiseless physical position
does not. Earlier receiver errors contribute to both conditioning problems, but
must not be added to the physical-position target. Carry the receiver state
continuously while removing only its future observation loadings for that target.
Hold future receiver transformations at the last earlier value under a named
policy; do not derive them from withheld coordinates. Keep the training covariance
prefix exactly unchanged. A singular future innovation is unsupported by the
current full innovations interface and must fail without a variance floor.

Report numerical completion, actual prediction errors, unidentified directions,
active bounds and unsupported uncertainty separately. A linear correction
outside the permitted calibration box receives no unrestricted covariance.
Intervals from an interior linear approximation are diagnostic until nonlinear
coverage is independently tested.

Then freeze a finite long-duration study. Keep the existing 10 m horizontal /
30 m height RMS accuracy screen, along with its maximum-error checks. Reserve
the exact starts, seeds, source/environment versions and native/packet work
before launch. Do not increase noise allowances or calibration bounds after
seeing outcomes. No aircraft measurements or protected flight groups enter
these software gates.

The initial source-law gate has closed. Its finite allowance and saved result
remain historical. The native remainder/error-law connection and the
long-duration gate each require a separate finite freeze of starts, source,
environment and work; this
page does not release an unbounded campaign.

[Training adapter](training-adapter-qualification/README.md) ·
[Work accounting](prepaid-native-qualification/README.md) ·
[Earlier noisy failures](../esa-noisy-prediction/INTERPRETATION.md) ·
[Prediction protocol](../PREDICTION_VALIDATION.md).
