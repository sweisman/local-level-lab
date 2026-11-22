# Test GPS trajectory approximation on the same force windows

Compare second- and fourth-degree position polynomials on the same 991
windows, both GPS motion sources and both packet clocks. Keep the original
epochs, packet intervals, cut between training and later data, and four field
and shape candidates. Use equal weights on the existing positions. Fit both
orders to each window before looking at accelerometer agreement.

Apply the original ±0.15-second timing allowance to conservative bounds for
the fourth-degree path. Save an eight-point Gaussian quadrature mean at
zero offset for each order. Compare the sampled means separately from the
enclosures so that permitting a wider force interval cannot by itself
explain an apparent improvement in the sampled comparison. The sampled mean
is a diagnostic with no integration error certificate.

Record how well each polynomial fits receiver height. Use the saved measured
force intervals and one 0–15% gain per recorder and candidate, under the same
two-sided rule as the [previous calibration](FORCE_INTERVAL_CALIBRATION_RESULT.md).
Score later windows at the training gain. Keep the onboard, phase and joint
profiles separate. Report sensitivity to trajectory order, receiver-motion
input and enclosure width. This cannot tell whether a higher-order fit has
captured real aircraft motion or GPS error shared by both streams.

Use one thread, 126,848 interval evaluations, 253,696 point evaluations and
72 bounded scalar profiles, with zero position solves or inertial fits.
Freeze the source, inputs and environment before replay.
