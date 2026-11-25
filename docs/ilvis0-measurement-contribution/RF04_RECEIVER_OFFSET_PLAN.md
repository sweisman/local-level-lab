# Diagnose the offset between the RF04 and Applanix receiver tracks

Use the two receiver coordinate series at the 443 original common UTC
times from the completed RF04 comparison. Use a local north–east chart
for this descriptive calculation. Report signed separation along the
RF04 direction of travel and to its right. Do not shift or interpolate
either receiver series.

Use centered RF04 velocity estimates wholly within each half of the
recording. On the earlier half fit three alternatives to Applanix minus
RF04 positions: a constant north–east offset, a velocity times constant
delay, and both together. Freeze those coefficients before scoring the
later half. Include the unadjusted separation on the same later rows.
Report the speed and course ranges, the amount of velocity variation
left after removing its mean, and how well the fitted models transfer.
The delay term is a first-order displacement approximation. A steady
flight can leave delay and a fixed position offset indistinguishable.
This comparison gives a relative diagnostic, separate from any Earth-model
fit or absolute receiver error estimate.

One local task, one numerical thread, five charged calculations, at most
443 rows each, and a 60-second cooperative cap. Reuse the sealed RF04
intake and selection, previous comparison receipt, and qualified task
recovery. Zero original IMU decodes, new Earth-model fits and reserved ESA
reads. [Previous motion check](RF04_MOTION_MATCH_RESULT.md)
