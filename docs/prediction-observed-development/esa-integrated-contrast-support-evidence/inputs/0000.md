# Check how accumulated velocity errors affect the forecast contrast

The [2.25 cm margin](ESA_COMPACT_FORECAST_MARGIN_RESULT.md) treats each
position error as free to change from one forecast time to the next.
The main term in the [integration budget](ESA_POSITION_BOUND_BUDGET_RESULT.md)
is an error in velocity. Its effect on position persists until it
cancels or is offset by a later velocity error.

Keep the certified compact contrast and the original chronological
times. Reconstruct its earlier weights through the frozen conditioning
operator. For every interval and axis, sum the position weights at all
subsequent times and multiply by elapsed time. This gives the exact
coefficient for an error in interval-average velocity. Use the full
position-weight sum for an error in initial position. Keep independent
position errors such as lever-arm differences as a separate term.

Use outward enclosures throughout and preserve the original certified
calibration gap. Report coefficients by axis and separate the intervals
before and after the forecast cut. Give the largest uniform allowance
certified for each source when the other sources are zero. These are
engineering limits for this one contrast. Physical velocity error bounds
across the full path, including the conditions needed to separate the
error sources, remain a separate requirement.

Freeze the completed compact result, original filter factors and
chronological times. One task uses one thread, three bound calls and
three charged steps, with a 180-second cooperative allowance. Reuse the
qualified recovery policy for one separately charged technical recovery.
Do not read new aircraft observations or start any fits.
