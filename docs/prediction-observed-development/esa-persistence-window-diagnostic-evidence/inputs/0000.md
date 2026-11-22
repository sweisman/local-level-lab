# Locate the two remaining ESA error misses

The [completed donor fits](ESA_JOINT_PERSISTENCE_ANALYTIC_RESULT.md) still
understate the error in one steady window and overstate it in one turn.
Use the existing forecast means, observations and fixed covariance settings
to locate where each error accumulates. This is a descriptive diagnostic on
the development flight. It uses no new fits and no reserved flights.

Apply the fitted time filter to each window and its extra covariance terms.
Then obtain sequential standardized innovations for each receiver epoch,
including the extra covariance in the conditional prediction. This allocates
the full score in time without assuming that the post-fit residuals are
independent. Check the sequence against a separate dense Cholesky calculation
on generated examples. Require its summed quadratic and log score to
reproduce the saved scores for all 16 window and input-convention combinations.

Report north, east and vertical contributions in that fixed conditioning
order, along with totals for each consecutive third of the window. Preserve
the order when comparing axes because the covariances can couple them. Show
whether the misses concentrate around a few epochs or persist through a
window, and compare the two misses with the six windows inside the reference.
Use recorded motion exposure for context. Treat all these comparisons as
descriptive, without choosing a new error law or threshold from them.

Freeze eight tasks with two 120-report windows each. Use at most two
one-thread workers, 32 charged calls and a 180-second cooperative deadline.
Bound dense conditioning to exactly these small windows. Keep the time,
standardized errors and motion exposure at every epoch in the sealed result.
Use an absolute replay tolerance of 0.000001 on both saved score quantities.
