# How much calibration information survives an earlier split?

Use the saved, sequentially whitened training derivatives from the
20 converged fits in the 400-report ESA development matrix. Compare the
whole 400-report derivative with the last 200 reports at each same fitted
point. Preserve the other four numerical outcomes as unavailable.

Also check the two completed 600-report specified-field fits of the
same recording. Compare their whole derivative with the last 400 and the
last 200 reports. Keep both fixed splits and both IMU noise assumptions.

For each split, measure the smallest and largest fractions of local
calibration information retained over all parameter combinations. Also
report conditional information for Z gyro bias and vertical accelerometer
bias after allowing every other fitted parameter to change. These
calculations diagnose local information loss and do not choose a split,
estimate aircraft variance or evaluate a future prediction.

Allow one thread, 22 sealed fit derivatives, 24 calibration windows and
zero fits, aircraft measurements, protected flight reads or native calls.
