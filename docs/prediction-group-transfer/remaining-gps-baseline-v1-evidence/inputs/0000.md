# Compare the twenty NASA recording groups with a GPS-only forecast

Use the exact twenty groups and both forecast cuts from the closed
[retrospective transfer study](REMAINING_GROUPS_PREDICTION_RESULT.md).
The GPS-only forecast uses the same fixed [spherical track rule](../receiver-only-geodesic-control/PLAN.md)
as the three-recording comparison. It extends the course and velocity
estimated from the final minute of earlier receiver positions. Save
each forecast before opening the separate scoring positions. Use the
same receiver epochs and error metric as the stored IMU forecasts.

Report results for all twenty groups at both cuts. Compare forecasts
when the original study selected a numerically passing IMU start using
earlier fit cost. Keep missing comparisons visible and preserve the
original absolute accuracy screen. Report the GPS-only and IMU errors
in metres. These are retrospective recordings, and the spherical
baseline uses no inertial values. This comparison cannot attribute an
advantage to the gyroscope alone or establish significance.

Freeze the archived parent study, selected IMU score ledger, source,
environment and separate training and scoring inputs. Allow 40 fixed
GPS extrapolations, one thread and a 120-second cooperative limit.
No IMU refits, new aircraft reads or reserved ESA data are needed.
