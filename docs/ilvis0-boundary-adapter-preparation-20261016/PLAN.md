# Saved-clock applicability screen for the remaining six

This screen uses the 22 primary/repeat endpoints selected in the completed
[stopping audit](../ilvis0-stopping-audit-20261016/README.md). It prepares the
geometry needed by the separately qualified two-sided stopping check, without
reading original recordings, integrating IMU increments or fitting observations.

For each endpoint, accumulate the frozen nominal 0.005-second intervals and use
the saved receiver epochs, time-offset scale and fitted normalized offset. Locate
the nearest representable clock transition by reproducing the native double
product, addition and left-interval comparison. Bisection stops at adjacent
representable inputs; it does not merge nearby epoch transitions. Select the
nearest transition by timing geometry alone, preserving any proposed relocation.

Find both adjacent constant-index intervals. Verify that the coarse/fine side
samples required by the new policy actually lie in those intervals and satisfy
its minimum representable separation. A C++ scalar clock reference checks the
Python clock calculations in independent software tests. It performs no IMU
integration or physical prediction.

Fixed allowance: **22 endpoints / at most 1,024 clock queries each / 22,528 total**,
one batch, four numerical threads, no retries. Freeze source, input and numerical
environment hashes first. Completed work renders metadata only. Errors stay
recorded; no wider search or larger query allowance follows.

Report supported geometry separately from numerical/scientific acceptance.
A nearby boundary is not silently substituted for the fitted point: any later
native adapter must charge fresh predictions, verify the relocation, preserve
physical bounds and compare the scheduled repeats. Smooth passing repeats in
different timing basins require separate profiling rather than relabeling.

This screen authorizes no native predictions, new observed fits or label changes.
