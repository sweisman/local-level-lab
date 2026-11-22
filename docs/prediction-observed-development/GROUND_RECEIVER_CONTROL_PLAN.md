# Ground interval receiver control

Use the hash-verified GNSS-only PPP export from opened ESA development
recording 187. Consider only the first 8,010 reports, the first fixed window
in the full-record receiver audit. Choose the longest consecutive run in this
window where reported horizontal speed is at most 0.5 m/s, absolute reported
vertical speed is at most 0.2 m/s, and adjacent report times differ by at
most 1 second. Break a length tie by choosing the earlier run. Require at
least 600 reports (about five minutes). Selection uses only time and the
receiver's velocity fields, never position scatter or IMU/model results.

For the selected run, express receiver latitude/longitude differences from
their median in local north/east metres using the WGS84 chart in which PPP
reports them. Report RMS, 95th percentile, one-minute block-mean range and
start-to-end displacement in north/east/height. Compare with the median
reported position standard deviations and record the selected run's speed
distribution and hashes. Run no model fit and read no protected group.

This is an exploratory **relative stability** check. The PPP position and
velocity come from the same solution, so velocity-based selection may favor
quieter position errors. The aircraft may move within the allowed speed
threshold; an absolute coordinate offset is unobservable. The result cannot
calibrate full-flight receiver coverage or the IMU error law.
