# Receiver-window threshold margins

Use only the sealed 53-stretch receiver-window inventory. For each of its three
candidate windows, publish the signed distance between the recorded vertical
velocity span and the fixed 1 m/s limit. Positive values are on the accepted
side of that one condition; negative values exceed it. Preserve the original
chosen window and every rejection reason. Check all published rows against the
sealed study hashes and record the reporter and output hashes.

Count selected windows and vertical-rate rejections within 0.02 and 0.10 m/s
of the limit as descriptive sensitivity summaries. These bins are for display,
not new acceptance thresholds. If every reported vertical velocity changes by
at most ε m/s, its span changes by at most 2ε m/s. The margins therefore bound
changes to the vertical-rate check alone. They do not measure receiver error,
cover course/speed checks, or establish stability of the complete selector.

This report reads no IMU increments, fused navigation, fit residuals or
protected confirmation data. It changes no interval, model comparison or
scientific decision.
