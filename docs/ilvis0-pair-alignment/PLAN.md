# Paired gyro alignment check

This saved-data diagnostic asks whether a constant relative orientation and
rate offset learned from the **earlier half** of each published same-track
recorder overlap predicts the **later half**. It does not refit an Earth model,
identify intrinsic sensor noise, or establish the physical installation.

Use the twelve frozen pairs and their verified per-second aircraft-axis gyro
caches from the paired time-scale check. Verify the pair CSV and every used
cache against the published receipts. Select only common complete UTC seconds
inside each published overlap; do not fill gaps. Split at the arithmetic
midpoint of the published overlap, before reading gyro values. Require at least
60 matched seconds in each half.

On the earlier half, fit a proper 3D rotation and constant three-axis offset
by weighted least squares (weight = shorter of the two bin durations). Center
both streams before the rotation fit. Also fit an offset-only reference with
the rotation fixed to identity. A rotation is identifiable only when the
centered earlier right-stream singular values satisfy s3/s1 >= 0.05. An
unidentifiable pair abstains from the rotated comparison but still reports the
offset-only reference. Preserve signed axis residuals, overall vector RMS,
training rank ratio and fitted rotation angle. Score the later half without
updating either fit. Do not choose the better method using the later data.
Also average held-out residuals in fixed nonoverlapping 10- and 60-second
windows, anchored at the first complete held-out second. Skip a window if any
second is absent. Report the number of complete windows and their vector RMS;
do not infer independent samples from adjacent windows.

The two streams are already mapped through their recorded IMU-to-aircraft
mount settings. Any extra fitted rotation may absorb mounting error, timing,
processing or actual motion differences. These pairs are related recordings,
not independent flights. This report cannot set the ESA error law or calibrate
Earth-model significance. Source originals and reserved ESA recordings remain
unopened; this is a read-only cache report with zero native calls and zero
model fits.
