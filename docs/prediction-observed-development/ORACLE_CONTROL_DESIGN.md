# Next software control: known calibration versus fitted calibration

The [known-answer forecast check](FIT_ADJUSTED_FORECAST_REPORT.md) found
50–84 m future horizontal RMS after four numerically passing generated fits.
The fitted sensor settings also differ from the generator's known settings.
The next test must separate error caused by recovering calibration from error
that remains when calibration is supplied exactly.

## Fixed comparison

Use the **same two sealed generated IMU streams** and their original query
times. For each stream, propagate once from the generator's true initial
state with its true fixed sensor calibration, time offset, lever arm and
gravity setting. Keep the random IMU errors already present in that stream.
Score reports 600–899 against independently generated future physical truth,
using the same north/east/up score as the saved fitted forecasts. Do not
re-fit, regenerate noise, add receiver data after report 599, or change the
saved fitted forecasts.

Before reading the long streams, a short clean generated control must show
that the oracle state and parameter mapping reproduce its known trajectory.
It must test timing, lever arm, gravity and all three gyro/accelerometer axes.
A failed clean control blocks the long comparison.

The short **2-second, 200 Hz clean software control now passes**. Two focused
tests verify the true-state gate and full native forecast with known timing,
lever, gravity and sensor corrections; the maximum coordinate error is below
0.01 m. The native kernel, forecast adapter and analytic-truth source bytes
also match the sealed parent study. This checks parameter mapping only. It
does not qualify the longer noisy-stream run or its restart policy.

This is a new finite study. Freeze its exact source/environment hashes,
two task IDs, input hashes, one native forecast call per task, a 243-million
packet-query-visit ceiling per task, at most two numerical threads total,
and cooperative wall limit. Qualify task-level restart after interruption,
with charged attempts and sealed completed results preserved. Do not expand
the completed fit-adjusted-control study's allowance.

The study identity is `esa-oracle-noisy-control-v1-20261115`. Its `increment`
and `point` tasks each reuse one sealed 900-second IMU stream, query the same
900 times and score only reports 600–899. The total allowance is two native
calls and 486 million packet-query visits, with two single-thread workers and
a one-hour wall limit. The shared recovery policy permits at most two charged
attempts per task and preserves completed results and failures. Source,
environment, parent manifest, input bytes and recovery qualification are
checked before launch or resume.

If the oracle forecast is substantially more accurate than the saved fitted
forecast on the same stream, examine calibration recovery and parameter
identifiability. If both drift, examine the motion model, noise and timing.
The comparison cannot calibrate confidence intervals or decide an Earth
model. The seven ESA confirmation groups remain reserved.
