# Receiver uncertainty across the opened development recording

Use only the already opened ESA recording 187 GNSS-only PPP export. Verify its
published SHA-256, parse every complete receiver report with the existing
strict parser, and divide the ordered reports into eight consecutive,
equal-count windows. Fix the windows before inspecting any statistics. Read
no IMU, model fit, withheld prediction or protected confirmation group.

Reuse the existing position-covariance and position-derivative-versus-velocity
audit in each window. Record dates/times, latitude, height, speed, reported
position uncertainty, covariance validity, derivative contrast and short-lag
correlation. Compare the first window with later windows for changes in the
receiver's own reported quality and internal consistency. Save source, plan
and code hashes with the deterministic result. No numerical fitting occurs
and the analysis uses one thread.

This internal comparison cannot measure true position error: position and
velocity came from the same PPP solution. It can test whether a single
stationary working receiver law is plausible across this development flight
and identify observable quality strata for a later frozen prediction design.
