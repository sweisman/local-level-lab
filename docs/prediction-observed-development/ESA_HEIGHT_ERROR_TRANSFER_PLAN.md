# Test whether forecast height errors repeat on the ESA development flight

Use the saved specified-field globe forecasts on recording 187. Compare
successive training cuts at receiver reports 200, 400, 600 and 800. For
each of the three transitions, test the increment and sampled-rate error
laws separately. Use the first 120 subsequent receiver positions at each
cut and check their times against the original receiver sequence.

Fit an offset and slope to the earlier signed height errors as a function
of time since the last training position. Save that correction before
opening the later scoring input. Apply it to the later height prediction
at the corresponding elapsed times. Report the raw and corrected height
errors and check that the horizontal errors agree exactly.

The test uses six charged corrections, one worker and one numerical thread
with a 90-second cooperative limit. It uses saved positions and forecasts,
with zero new fits, propagations, original-file reads or reserved-flight
reads. Preserve the original fit and accuracy outcomes. Both error laws
use the same flight, and an earlier forecast's scoring period can inform
training at the next cut. The study tests transfer across time within one
recording. It establishes neither new decision thresholds nor coverage on
independent flights.
