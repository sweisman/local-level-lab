# Full opened-flight parallel receiver comparison

Use only ESA development recording 187 and its three already retained
GNSS-only PPP exports: `air1`, `mosaic03` and `pwrpak7`. Verify each original
source hash from its saved inventory or acquisition receipt. The air1
reference has 64,080 reports. Divide it into the same eight consecutive,
8,010-report windows frozen by the full receiver-consistency audit. Reject
any changed source, count, window boundary or non-increasing time.

For each window, match each other receiver to air1 by recorded GPS time
within **2 milliseconds**, without interpolation or reused reports. Report
match counts, maximum absolute time offset, raw local north/east/up position
differences and the same first-order time adjustment used in the earlier
400-training-epoch comparison: subtract the other receiver's reported
velocity times its signed time offset. Record per-axis mean, RMS, centered
RMS, 95th absolute percentile and lag-one correlation. Keep the windows
and both other receivers even where a result looks unfavorable.

This is a relative agreement check among separate receivers on one antenna
and potentially shared PPP processing. It cannot measure common position
error, true aircraft position, IMU error or Earth geometry. It does not open
any reserved ESA group, fit an Earth model, set a calibration threshold or
revise the frozen 400-epoch result. The goal is to see whether the relative
receiver discrepancy and its time dependence remain similar during flight.

Work limit: three original-source hash checks, three stream parses, zero
model fits, one numerical thread. Save plan/source/code hashes and all window
summaries. Failure remains recorded under this method; changing the matching
or adjustment requires a new identity.
