# What the long-motion controls establish

All 48 twenty-minute cases pass the unchanged checks. They cover every candidate,
both latitude signs, both removal cases, climbs and descents, and both gravity
laws. The run used 144 native calculations in 38.87 minutes.

The unchanged value calculation has maximum spatial errors of 0.109 m at 300 Hz
and 0.0273 m at 600 Hz against independent analytic positions. The wider tangent's
300 Hz positions agree with that value calculation within 0.0000383 m in the
reported coordinate-scaled comparison, retaining all 27 derivative columns.
These are software checks with true corrections supplied, not measurements of
instrument noise or calibration accuracy.

The separate training adapter also passes its 20 source-bound checks. Those
include four native tests that change later positions only after saving the
forecast: training and forecasts remain identical, while scores change.

The next gate is a full matched training study. It must estimate calibration
without being given the true state, pass the original stopping checks, and
predict unused positions within the original limits. No original aircraft fit
has been reclassified, and all seven confirmation groups remain protected.

[Verified report](README.md) · [Training study](../esa-wide-training-controls/README.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
