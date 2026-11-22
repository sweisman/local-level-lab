# Single-pass ESA conditional-forecast check

The [first attempt](CONDITIONAL_FORECAST_V1_RESULT.md) stopped at 600,000
native calls before producing a forecast. This is a separately frozen
technical revision of the **same scientific question** and recording.

Build the fixed IMU-plus-receiver error operator once over all 1,200 GPS
query times, using the same training-only initial state, 800 early receiver
rows, saved IMU increments, model, clock, receiver transforms, noise law and
calibration bounds. Verify every early input hash and require the resulting
operator's 800-epoch prefix to match the sealed training operator exactly.
Apply only the saved 800 earlier receiver-minus-trajectory errors to the
operator. Save the 400 conditional receiver means, fixed-parameter marginal
covariances and original uncorrected trajectory before any later receiver row
is opened. No parameter fit, new forecast trajectory, error-law tuning or
model selection is permitted.

A separate reporter will open the same previously sealed later GPS reports
and score the conditional receiver mean and the raw trajectory on the same
400 times. The physical-accuracy screen is descriptive, not calibrated
coverage. The result remains a development diagnostic and the Earth-model
decision stays **abstain**. Seven ESA confirmation groups remain reserved.

One task, one numerical thread, a one-hour cooperative limit, at most
450,000 native calls and 1 billion packet visits. Qualify exact early-only
inputs, prefix equality, error-budget preservation and reboot recovery before
launch. Do not resume, alter or erase the first terminal attempt.
