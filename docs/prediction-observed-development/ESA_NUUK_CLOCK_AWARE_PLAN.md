# Check a receiver-common Doppler offset on the fixed Nuuk interval

Keep the sealed 100-second comparison as the original result. Apply a
separate screen to the same 120 seconds and the same candidate satellites,
aircraft ranges, orbit and clock products, and score. For each satellite,
estimate a shared phase–Doppler gap using the median gap of at least five
*other* supported satellites that meet the original lock, signal and
two-band requirements. With fewer peers, keep the original check. Apply
the original 0.35-cycle threshold to the difference from that estimate.
Keep all other checks, including the 0.075 m two-band limit. Use original
phase and code measurements to evaluate the carrier ranges.

First verify the screen on a common shift, an isolated satellite slip
affecting both bands, a single-band error, loss of lock, and too few peers.
Report support gained or lost, whether the original common-satellite
ranges reproduce, and the nearby-station disagreement and score bounds.
Show the newly admitted seconds separately. This is a development
sensitivity check on the same recording. It supplies no independent
aircraft error limit and does not qualify use on reserved flights.

Use one local task and one numerical thread, with one setup, 120 interval
checks, three conditional bounds, and a 60-second cooperative cap. Preserve
the original limits and sealed evidence. No new Earth-model fits, network
transfers or reserved data reads.
