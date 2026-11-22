# Check later forecast errors against a second receiver

Use the sealed 20-group development study and the eleven verified receiver
pairs. Join them by original recording SHA-256. Keep all twenty groups in the
inventory, including any group without a passing later-cut forecast or an
overlapping receiver. Compare the saved specified-field globe forecast only.

Match GPS epochs exactly using the original saved UTC tags and the recording's
GPS–UTC offset. Score both references on the same matched later epochs. Use at
least two aligned earlier and two aligned later epochs. Retain the unscored
counts and the time of the first and last supported forecasts. Do not fill gaps.
Estimate a constant relative receiver offset using only the matched earlier
epochs and show scores with and without that offset removed. Apply the original
forecast scoring metric to all references. Report both horizontal and height
RMS and the relative receiver difference after the offset correction.

A partial overlap tests sensitivity on the matched epochs only. It cannot
validate the original full-horizon decision or measure errors shared by the two
receivers. This study limits work to twenty existing groups, eleven source pairs,
at most one saved forecast per group, and three reference scores per forecast.
Use one numerical thread and no new fits, source decoding or position solves.
