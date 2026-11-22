# Check how the recorded packet bounds grow

The [short preflight](ESA_SOURCE_TRANSFER_CHECK.md) matched both forecasts
at the first two query times. Before running the full 155,868-packet history,
check the size of the position remainder at four fixed points on the same
recording. Use original query numbers 1, 2, 5 and 10, roughly 0.55 to 9.55
seconds after the start. Keep both zero-field candidates, the same initial
states and all 27 calibration bounds from the preflight.

The first two queries repeat the original position checks within one
micrometre. Use sealed predicted positions and all 27 derivative columns
as the reference at every query. Retain the shared coefficients as well
as the unshared remainder. Compare the largest coordinate remainder with
the earlier [4.03 cm engineering target](SHAPE_REMAINDER_METRES_RESULT.md).
This is a sufficient target under the earlier assumptions. Exceeding it
indicates the current proof is too wide at that query. It does not measure
the true error or change either model's scientific outcome.

Use the original arithmetic after the width-cache speed gate failed.
Freeze two tasks with at most 3,200 packets and 6,400 packet steps per
candidate, one bound charge each, two one-thread workers, 480 seconds per
bound and 550 seconds overall. Save each checked query as it finishes.
Keep partial reports if a calculation stops. Use the qualified technical
recovery rules. There are no new fits, measured position reads or reserved
flight reads.
