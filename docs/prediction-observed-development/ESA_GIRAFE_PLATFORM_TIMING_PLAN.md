# Match the platform clock to a separately timed force record

The [layout audit](ESA_GIRAFE_PLATFORM_PROBE_RESULT.md) places three
small excerpts on one relative clock. To test its connection to the
flight, use the same three byte offsets in the opened recording and
allow up to one MiB per offset. Keep the complete interior records,
report both acquisition edges and verify their timestamp phase against
the saved probe. Keep the original ranges and acquisition receipts locally.
Use the same authenticated archive, verified source size and trusted
certificate as the smaller probe.

Use the verified 10 Hz Nuuk–Reykjavík GIRAFE acceleration record as the
time reference. Treat the first three values after the platform timestamp
as a candidate force vector. Check their changes without relying on an
Earth model or the last three platform columns. Compute a time-weighted
force-magnitude series on tenth-second supports, then compare its
centered first differences with the first differences of the 10 Hz
reference magnitudes. Timestamp each platform average at the center of
its tenth-second support. Preserve
the exact time tags, sampling, duration and fitted amplitude in the receipt.

Estimate the time offset by searching the whole verified 10 Hz record
using only the first longer excerpt. Save the highest correlation and
the best alternative separated by at least two seconds. Require a
correlation of at least 0.70 and a separation of at least 0.10 before
using the first excerpt as an anchor. Freeze that offset for the next
two excerpts. Each must reach 0.70 at the nearest predicted reference
sample and put its independently found peak within 0.2 seconds of the
predicted time. Report failed or ambiguous
matches. The thresholds are a development screen for locating the log
on the flight clock. Fine timing, axis mappings, angular-rate units and
direction accuracy need further checks before any shape comparison.

Before the observed alignment, test the matching code on generated
signals with a known offset, distinct repeated features and a holdout
with a changed clock. Freeze both the acquisition and matching allowances.
The scope is the opened recording 187 and the two GIRAFE streams listed
here. Reserved recordings and model scores stay outside the alignment.

Allow one task, one thread and 180 seconds. Charge three reads of exactly
1,048,576 bytes, one verified read of the 16,883,030-byte reference, and
three searches of at most 234,193 reference epochs each. Fit neither a
clock drift nor a sensor calibration. Store full search results by peak
and prediction score and keep the source excerpts in the local evidence
directory.
