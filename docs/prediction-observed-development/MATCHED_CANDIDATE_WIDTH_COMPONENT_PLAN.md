# Saved range-width component audit

Question: Which declared uncertainty makes the completed three-model generated
receiver ranges too wide to separate?

Use the sealed 12-recording study only. Its bounded affine calculation adds a
conditional future-noise radius to a calibration allowance. Recompute the
future-noise radius from each saved receiver-target covariance and the frozen
whole-path Gaussian allowance. Subtract it from half of each saved interval
width, checking that the decomposition stays nonnegative. Summarize the
calibration share of the horizontal range at withheld epochs 1, 10, 20 and
40, preserving every candidate and recording in a report.

This is exact bookkeeping **within the assumed affine Gaussian calculation**.
It does not measure the aircraft's error law, identify an individual sensor
parameter, narrow an interval, make a model decision or run new fits.
