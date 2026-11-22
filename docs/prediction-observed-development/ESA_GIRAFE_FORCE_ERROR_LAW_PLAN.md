# Test whether the measured force error transfers to later windows

Use the eight sealed GIRAFE–iMAR overlap windows on ESA recording 187.
Order them by their frozen UTC start. Use the first four windows to learn
the GIRAFE-minus-iMAR offset and error covariance. Score the last four
as complete withheld windows. Use the same 16 supports on each one,
both original averaging widths and the declared clock alignment.
Use the iMAR force mapped to GIRAFE's documented location. This is
a retrospective development test on one previously examined flight.

Both error laws use the mean of the four training windows. The first
uses one independent variance at each support, with the estimated
mean's sampling variance shared across the held-out window. The second
has a correlated within-window component and a constant window-level
component. Estimate lag-one correlation after removing each training
window's mean, constrain it to ±0.95, and use powers of that correlation
at successive supports. Estimate within-window and between-window
variance by moments, truncating negative estimates of the window-level
component at zero. Carry the shared uncertainty from estimating the
earlier mean into both predictions.

For each later window, report the offset prediction, the residual RMS,
the negative log score per support and the mean squared standardized
error for both laws. Also report the observed window mean with each
law's working 95% range. These are comparative development scores from
a dependent dataset. The working ranges do not establish true
instrument uncertainty or independent-flight coverage.

Freeze two tasks, one per width, with one ledger operation per task
and up to two covariance estimates from the earlier values. Allow one
numerical thread and a 60-second limit. Use only the already saved force
magnitudes. No instrument reread, model fit, protected flight or change
to a previously frozen error policy.
