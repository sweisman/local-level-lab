# Check the sealed predictions against the recorded angles

Use the eight [sealed receiver windows](ESA_DIRECTION_HOLDOUT_FORECAST_RESULT.md)
from ESA development recording 187. Verify the original iMAR file size,
hash and fixed-line format. Read only the angular rate and specific force
needed to bracket each window, with 50 ms of padding. Reject gaps above
5 ms, duplicate or reversed clocks and insufficient coverage. Preserve a
failure with its cause and keep the other selected windows in the report.

Construct increments from the 300 Hz rate samples with the original
trapezoidal rule. Integrate the measured rotation to bring accelerometer
vectors into a common frame, and average with the same receiver time
weights as the forecasts. Compare the 28 pair angles from the last eight
directions. Compute the angles twice, with the original accelerometer
position and with the previously published fixed antenna correction.
Use nominal calibration and apply the same measured angles to every
shape and field prediction.

Report each model's RMS angle error, the difference between their errors,
and the size of the change in measured angles that would tie the two
scores. Compare each error with the corresponding earlier error reference
already sealed. Retain the zero-field comparison separately and keep the
two specified-field settings separate. A model can have the lower error
and still exceed the reference. Use these results to assess transfer of
prediction accuracy within one installation. The 28 angles share eight
directions, the settings reuse the same data, and both legs belong to
one recording. No independent-flight accuracy or scientific decision
follows from this check.

Freeze a maximum of one full hash pass over 1,100,258,400 bytes and
eight selected measurement operations of up to 121,000 original sample
intervals each. Each operation includes construction and scoring.
Run one worker and one numerical thread under a 150-second ceiling.
Charge before each operation and save each window's result as it finishes.
No new calibration, navigation fit, receiver reread or reserved group.
