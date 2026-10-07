# Measuring how long errors last

A noisy IMU reading may differ from the next reading by chance. Another error may
persist for minutes. Those two situations behave differently: averaging many readings
helps much more when their errors are independent. GPS errors can persist too, and
GPS is used to distinguish aircraft acceleration from a change in IMU tilt.

The latest saved-recording study found that all model fits worked numerically, but
the apparent strength of the comparisons changed substantially with the assumed
duration of the errors. We therefore need measurements of error persistence, rather
than choosing the assumption that gives the strongest model separation.

## What to record when the instruments arrive

First perform the [instrument checks](BENCH.md), especially the independently imposed
slow-rotation test. For persistence measurements, record each IMU resting untouched
on a firm surface for at least two hours. Keep its orientation fixed, record its
temperature, and retain the original recording. Repeat on different days and identify
the physical unit and settings used. A steady room temperature is useful for the first
recording; warming-and-cooling tests answer a separate question about temperature.

If possible, let the phone record GPS in the same session where reception is good.
The analysis can still characterize the IMU when GPS is absent. GPS observations
must be retained as received, including gaps and accuracy fields.

Use an explicit still phase in the recording. A phase marker declares the intended
experiment; someone must also check that the apparatus really remained still.
Do not use a moving flight as though it were a stationary noise measurement.

## What the diagnostic reports

The research tool averages observed samples into complete seconds, then reports
how much different channels vary together, how readings relate across time, and
how variation changes when readings are averaged for longer. It checks lags of
1, 5, 15, 60 and 300 seconds, alongside the same-second measurements. The block
averages cover 1, 15, 60 and 300 seconds.

It reports two views: after removing a constant average, and after also removing
a straight drift trend. Both are retained because removing a trend can hide the
slow error we need to understand. Temperature range is recorded alongside them.

Missing, incomplete or saturated seconds stay missing. The tool never fills them
in, joins observations across a gap, or mixes different still phases. A channel
that never changes has undefined correlation; it is not proof of a perfect instrument.
When GPS is available, its channels and the simultaneous GPS/IMU channels are
reported separately so shared variation is visible.

Run this from the repository root, using a new output filename:

```sh
env OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONPATH=analysis \
  ~/venv/bin/python analysis/tests/characterize_input_persistence.py bench-session.zip --output bench-persistence.json
```

The output retains the source recording hash and diagnostic version. Existing output
files are not overwritten. Keep the original recording with the report.

## What this does not establish

The tool is ready and has nine controlled software tests. **No real instrument
recording has been characterized with it yet.** Its output describes the recorded
variation; vibration, mounting movement, temperature and drift can all contribute.
A still GPS recording does not measure the errors of an airborne receiver, and it
does not characterize gaps or interpolation in public airline tracks.

The lag estimates reuse observations. Their finite-sample values are not an automatic
noise model or confidence bound. The tool does not choose a correlation duration,
approve an IMU, set a decision threshold or decide between Earth models.

Repeated measurements and motion controls will help define defensible uncertainty
assumptions for the research correction. Those assumptions must then be frozen before
fresh calibration and independent validation. The [completed saved-recording study](covariance-refits-20261007/README.md)
explains the model-separation problem that remains.
