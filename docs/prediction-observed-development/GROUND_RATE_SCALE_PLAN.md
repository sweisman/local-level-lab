# Logged gyro variation across averaging times

This is a fixed, descriptive extension of the two receiver-selected ground
controls in opened ESA development recording 187. Use their already saved
IMU-overlap boundaries unchanged: `ground-imu-rate-result.json` for the first
stop and `second-ground-imu-result.json` for the second. Verify both result
hashes, the original iMAR source hash, and the strict parser source hash.
Read the original stream once. Do not inspect any reserved flight group.

For each stop, average raw instrument-axis angular rates into consecutive
1-second, 10-second and 60-second bins anchored at its saved start time.
Retain a bin only when it contains at least 95% of the nominal 300 Hz sample
count. Reject non-increasing timestamps or a within-stop gap above 1.5
nominal periods. For each bin scale, record the number of complete bins,
standard deviation of their three axis means, and the adjacent-bin Allan
deviation: the square root of half the mean squared difference between
consecutive bin means. Check the complete 60-second bin means against the
previously saved minute summaries. Save source, plan and code hashes.

These statistics include any aircraft turning, mounting motion, temperature
effects, instrument offsets and upstream processing. They are **observed
logged-rate variation**, not a sensor-only noise specification or a measured
background field. Compare their change with averaging time to the white-noise
`1/sqrt(time)` reference only as a diagnostic. Make no calibration prior,
Earth-model decision, field estimate or solar-versus-sidereal claim.

Work limit: one full-file hash, one full-file parse, zero fits and one
numerical thread. The source and interval summaries remain saved if this
diagnostic fails; an altered method requires a new result identity.
