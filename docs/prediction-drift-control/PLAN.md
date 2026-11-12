# Can an earlier residual trend predict later error?

This finite saved-data diagnostic tests a specific possible error process.
The previous three-recording pilot and receiver-precision audit show smooth
later forecast errors, but a trend fitted to *later* errors cannot predict a
flight. Here the only estimated corrections come from the last 120 seconds of
the original earlier training block. The later block is used only for scoring.

Reuse the 36 already frozen model, clock and processing settings and their
training-cost-selected starts from the receiver-precision audit: 28 qualified
starts and eight numerical abstentions. Do not reselect a start using later
errors. For each selected start, calculate three later error scores on the
same saved one-second epochs:

1. Original uncorrected forecast error.
2. Subtract the mean training residual from the final 120 training seconds.
3. Subtract a straight-line training residual extrapolated from that same
   window using the actual timestamps.

Use ordinary least squares independently on north, east and height. Require
at least 100 training epochs in the fixed window and a nonzero time span.
Report per-axis, horizontal and three-dimensional RMS, as well as the
fraction of settings improved and worsened. Preserve every individual result.
Check the uncorrected score against the closed pilot before reporting a
correction. This is an empirical receiver-residual correction, not a new
physical Earth model or a replacement for the original model score. It may
absorb model error and shared GNSS error; no resulting preference is a
scientific decision. The three recordings are retrospective development data.

Freeze three segment tasks, no native calls, no model fits, no original IMU
reads and no protected ESA reads. Use one thread, a ten-minute wall ceiling,
source/environment hashes, source-bound software tests and qualified
task-level recovery. Publish all 36 settings, including abstentions, with a
verified receipt. The result can support or reject this simple *predictable*
drift candidate; it cannot calibrate coverage or identify the drift's cause.
