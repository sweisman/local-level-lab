# Test whether the fitted calibration transfers across the development flight

Use all four sealed straight-course controls and all four sealed turn
controls on the opened recording 187. Use the 400 earlier receiver
reports of each control, excluding the 120 reports scored by the original
position forecasts. Confirm that the windows do not overlap one another
or the window that set the calibration. Keep the existing 16 force
supports, relative to the start of each window, and both 11- and 25-report
averaging widths. Use the archived receiver export velocity present in
all windows. Neither file selection nor averaging uses angular errors.

For each matched field and shape, transfer the exact 12-coordinate
calibration from the corresponding all-source pooled fit. Keep those
parameters fixed on every window. Start a separate orientation frame on
each window by aligning the first eight force directions. Score the eight
later directions with that orientation held fixed. Also run the nominal
sensor calibration with the same starting-orientation rule. Compare angular
RMS, paired shape ranking and changes from nominal. Keep results for all
windows, including those with maneuvers or weak orientation information.

Freeze eight tasks, at most 13 packet passes per task with at most 121,000
intervals per pass, one numerical thread and a 180-second ceiling. No gyro
or accelerometer calibration is re-estimated, no original data file is
opened and no reserved group or original position holdout is used. The
windows test within-flight transfer. A spread across them is a development
diagnostic and does not establish a bound on independent-flight errors.
