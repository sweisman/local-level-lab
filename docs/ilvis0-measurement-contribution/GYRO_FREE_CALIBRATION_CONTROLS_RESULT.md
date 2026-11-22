# Gyro-free calibration predicts known later forces

All eight generated cases passed. One calibration fitted to the earlier
packets predicted the later force to within **2 × 10⁻¹⁵ m/s² RMS** in
every case. When the later required force was changed by 0.025 m/s², the
same calibration missed it by 0.025 m/s² RMS. Both clocks passed, and
each fit saved its calibration before opening the later data.

The controls use exact force histories with changing sensor directions.
They verify that the two sides of the comparison use the same time
support. Twenty-one focused software tests passed, including the check
that a correlated force covariance remains in the objective and a check
against the exact average of a rotating force. The latter verifies a
bound for the error caused by packet averaging when a limit on how fast
the force vector changes is supplied.

The study used 152 training evaluations and 16 later checks. It ran no
recorded-aircraft fits. Aircraft use still requires a supported motion
limit, GPS derivative uncertainty and accelerometer error bounds. The
precision above describes the generated calculation.

[Frozen method](GYRO_FREE_CALIBRATION_CONTROLS_PLAN.md) ·
[Saved results](gyro-free-calibration-controls-result.json) ·
[Reproduction bundle](gyro-free-calibration-controls-evidence/bundle.zip)
