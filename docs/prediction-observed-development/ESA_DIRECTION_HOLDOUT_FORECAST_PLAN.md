# Seal the angle predictions before reading the gyro

Use the [eight selected windows](ESA_DIRECTION_HOLDOUT_SELECTION_RESULT.md)
and the same receiver processing as the
[matched differentiation check](ESA_MATCHED_RECEIVER_RESPONSE_RESULT.md).
Use only the primary `air1` receiver export from development recording 187.
Check its full source hash, the selected report indices, the GPS week,
the one-second spacing and the original receiver sequence. Verify the
queries lie within the documented IMU clock span. The actual inertial
clock and sample continuity get a separate check when the IMU is read.

Calculate the receiver-derived direction angles using both averaging
widths, both differentiation methods and all three background-field
settings. Save the globe and disc predictions for all 28 pairs of later
directions without reading the measured IMU data. Score the magnitude of
the angular prediction errors later, with and without the same fixed
antenna offset. Repeat the zero-field comparison first and retain the
specified-field comparisons separately.

For each setting, freeze a descriptive error reference using the eight
earlier windows. Take the smaller of the two absolute RMS angle errors
in each earlier window, then take the largest of those eight errors.
Report whether either shape predicts the new angles within this fixed
earlier error range and report how much the two shapes differ. A large
absolute error can coexist with a small advantage over the other shape.
The reference measures transfer of previous performance. An accuracy
standard for independent flights still needs separate support.

Allow one complete receiver scan of 64,080 rows and 16 paired-method
operations, each charged before evaluation for its full quadrature work.
Freeze the two receipts, source binding metadata and code. Use one worker,
one thread and a 90-second ceiling. This phase reads zero original gyro
files and zero reserved groups. It performs no navigation or calibration
fits. The sealed prediction receipt defines the inputs for later scoring.
