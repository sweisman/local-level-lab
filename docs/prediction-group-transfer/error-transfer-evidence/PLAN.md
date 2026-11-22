# Test whether forecast error repeats across two cuts

Use the same two chronological forecast cuts in all twenty groups from
the [sealed transfer study](REMAINING_GROUPS_PREDICTION_RESULT.md). At each
cut, keep the passing start chosen by the original earlier training cost.
Where no start passed stopping, use the lowest earlier training cost for
a separate diagnostic and preserve the failed status. Start index breaks
ties. No later error enters the choice.

Fit one offset and one slope per axis to the earlier forecast's signed
position errors as a function of seconds since its training cutoff.
Transfer that correction to the same elapsed times after the later
cutoff. Save the correction before opening the later scoring errors.
Compare raw and adjusted horizontal RMS, height RMS and both peak errors
against the unchanged descriptive accuracy screen. Report all twenty
groups and the five with passing starts at both cuts separately.

This tests one simple error correction on separate time blocks of a
recording. It does not measure intrinsic gyro drift, qualify a correction
for other flights, establish statistical coverage or change any original
model outcome. The earlier scoring period may be part of the later
forecast's original training period.

Freeze the original verified ledger, selected error segments, source
and environment. Use one thread, 20 task identities, 20 charged
correction calculations and a 90-second cooperative wall limit. Use no
navigation fits, propagation, original recordings or protected flights.
