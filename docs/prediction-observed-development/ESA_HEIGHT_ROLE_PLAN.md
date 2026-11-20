# Check how height affects two saved ESA forecast results

Use development recording 187 and the first 120 withheld GPS positions
at each of two different cuts. Keep the cuts and their error laws separate.

- **After 800 reports.** Determine whether the saved mean adjustment or
  the small stated height width contributes to the short-horizon misses.
  Compare raw and adjusted height errors against the exact same saved
  adjusted marginal widths. Report the fractions inside and out, the
  net contribution of the adjustment to squared height error, and
  whether individual epochs enter or leave the band. The raw comparison
  reuses widths for diagnosis. The experiment leaves the raw forecast's
  uncertainty unspecified.
- **After 400 reports.** Reuse every saved candidate forecast, its earlier
  condition, original reference positions and four working covariance
  settings. Calculate the joint score with all later coordinates, then
  compute the joint score using only north and east. This requires the
  marginal north/east covariance across time. Setting later height errors
  to zero in the full score would still use height information. Verify the
  full score against the original replay and record its difference from
  the horizontal score. Keep all training observations and earlier-only
  start selections. Retain both incomplete comparisons as incomplete.

The scores test retrospective sensitivity. They leave the absolute height
check, physical calibration and flight-to-flight uncertainty in force.
Neither check introduces a replacement range or threshold.

Freeze the verified inputs, numerical environment and source. Use five
tasks with one thread and a 90-second cooperative allowance. Charge one
height audit and four covariance factorizations and 80 path scores,
each on at most 360 coordinates. Use zero native navigation calls,
original-flight-file reads, and reserved-flight reads.

Verify the score decomposition against a separate dense calculation on
a small, correlated generated case. Verify that changing a withheld height
leaves the marginal horizontal score fixed. Then check the saved full
scores and the nominal 25/120 height count during the replay.

[Matched range audit](ESA_MATCHED_UNCERTAINTY_RESULT.md) ·
[Original whole-path scores](ESA_JOINT_PATH_SCORE_RESULT.md)
