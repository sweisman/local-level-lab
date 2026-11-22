# Long clean forecast control

The known-calibration forecasts on two saved noisy generated streams still
drift. This control tests whether the same physical trajectory drifts without
injected IMU or receiver error.

Generate one 900-second, 300 Hz IMU stream from the existing analytic rotating
globe truth with fast motion, climb, inverse-square-height gravity, fixed
known sensor corrections and no random errors. Use the same 900 half-second
offset receiver query times as the noisy studies. Propagate once from the
known initial state and corrections. Score only reports 600–899 against
independently generated physical receiver truth. No parameters are fitted and
no later receiver positions enter the forecast.

Freeze one task with one native forecast call and exactly 243 million
packet-query visits; generation is limited to 270,601 truth samples and
270,000 constructed intervals. Use one numerical thread, a one-hour wall
limit and source/environment hashes. Require passing source-bound software
tests and separately qualified task-level reboot recovery before launch.
Do not alter the completed noisy or fitted studies or read protected ESA groups.

A close clean forecast would isolate the noisy-stream failure to injected
errors or their interaction with the forecast. A drifting clean forecast would
prioritize the long-duration motion, timing and gravity implementation.
Neither outcome calibrates coverage or decides an Earth model.
