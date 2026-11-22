# Check whether raw carrier differences explain differences in GPS positions

In the [same-flight covariance comparison](ESA_ADDITIVE_RECEIVER_COVARIANCE_RESULT.md),
the combined model improved predictive scores but gave the original
GPS receiver too much uncertainty. The
[archived raw carrier comparison](ESA_PARALLEL_RAW_RECEIVER_RESULT.md)
provides a different check on what originates in the receivers and what
arises in the processing that produces their position solutions.

Use only the previously archived three-receiver raw carrier comparison
on ESA recording 187. Keep its fixed 519 one-second intervals, its
common satellite lists and the exclusion across the documented clock
step. The interval is separate from the eight forecast windows and
comes from the same flight. Match the three original precise point
positioning (PPP) exports at both ends of each raw interval. Use the
already documented time tolerance and correction from reported velocity.
Keep unmatched intervals separate. Verify all input hashes before use.

At each endpoint, project the signed position difference between
receivers onto the same satellite lines of sight from the archived
broadcast orbit calculation. Difference those projections across the
interval and remove one receiver-clock difference in the same way as
the raw carrier comparison. Compare this predicted range difference
with the recorded clock-removed carrier difference for each of the
three receiver pairs. Report RMS error, signed agreement by axis from
the common geometry, and score relative to predicting zero difference.
Summarize earlier and later intervals separately. The satellite
differences share a clock estimate within an interval, and all
receivers share one antenna. Keep these comparisons descriptive.

Do not refit the aircraft forecasts, change the receiver covariance
or open another flight. Matching carrier changes can constrain the
relative origin of position differences. Errors shared by all three
receivers and a common position bias remain outside this comparison.

Keep the published broadcast ephemeris selection, geometry condition
limit and receiver clock centering. Use a local north, east and up
decomposition with the same clock column for both predictions. Skip a
fixed interval for every receiver pair if any endpoint lacks a match or
any satellite in the frozen list lacks healthy broadcast geometry.

Freeze the signed carrier observations, original broadcast inputs,
matched position rows, software checks and environment. Use one task
for each of the earlier and later portions, run by two one-thread
workers. Charge one call and three steps per interval, including skips.
Allow 180 seconds, with at most one additional attempt per unfinished
task under a separate 180-second technical recovery allowance.
