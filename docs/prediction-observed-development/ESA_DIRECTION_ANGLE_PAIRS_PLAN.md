# Compare force-direction changes without fitting a starting rotation

The eight sealed ESA development windows already passed a comparison that
fits an initial orientation from their first eight averaged directions.
Test the same physics without that fitted rotation. Within each window
use all 28 pairs of the last eight preselected directions. For each
pair, subtract the predicted angle between the two directions from the
measured angle. Report RMS mismatch in degrees. A common three-dimensional
rotation leaves every pair angle unchanged. The comparison loses some
directional information and pairs sharing a direction are dependent.

Use both original averaging widths, all three matched-field settings
and the archived receiver velocities. Use nominal sensor calibration so
all models see the same measured angles. Check that the flexible
orientation fit at nominal calibration reproduces the earlier archived
score before releasing the comparison. This study tests the role of
fitted orientation on one previously examined flight.

Add the angle calculation to `force_direction_alignment.py` and test
known angles and rigid-frame invariance. Share the window reader with the
fixed-calibration transfer evaluator. Run the new evaluator with
`lll.studies` using the already frozen window inputs and expected scores.
Freeze eight tasks at one packet pass each, up to 121,000 intervals per
task, one numerical thread and a 120-second ceiling. No new sensor
calibration, original-file access, unused position holdout or reserved
group. Retain all window rows and abstain from a scientific decision.
