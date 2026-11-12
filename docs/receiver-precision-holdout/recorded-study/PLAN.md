# Compare withheld forecast errors with receiver precision reports

This is a saved-data adequacy diagnostic for the three recordings already
selected in the retrospective prediction pilot. It performs **no new fit**.
For every model, clock and processing setting, choose a numerically qualified
start by its earlier training cost alone. Retain all 36 settings, including the
eight without a qualified start; do not choose a setting because its later
error is small. The closed pilot currently supplies 28 qualified primaries.

Use each recording's checksummed primary-receiver enhanced-position table from
the separate 53-file precision inventory. All three tables passed that
inventory. Match each saved one-second pilot epoch to the same receiver's
binary report by its exact GPS week and millisecond tag. For these 2009–2010
recordings, freeze GPS minus UTC at 15 seconds. Permit at most 20 ms tag
difference, no interpolation and no silent epoch removal. Verify the match
using the earlier receiver coordinates from the frozen pilot input, before
using any later forecast residual. A task must account for every later epoch;
if a report is absent, record the gap and fail the complete-support gate.

For each qualified primary report later north, east and height RMS errors;
receiver-reported one-sigma scales; normalized RMS by axis; residual
autocorrelation at one, five and thirty seconds; and the fraction above one,
two and three reported sigma. Group results by the three conservative flight
groups, and keep numerical failures and physical-accuracy labels visible.
The receiver's sigma is its **own estimate**, not an observed truth error.
Residuals combine IMU error, model error, receiver error and common GNSS
effects. This comparison is descriptive; it cannot by itself calibrate
absolute GNSS accuracy or give a model significance level.

Freeze three tasks, one per original recording, each reading only saved pilot
and receiver-inventory evidence. No original IMU reads, model fits, native
calls or protected ESA recordings are allowed. Bind the selected start IDs,
source hashes, receiver-table hashes, timing rule, environment and exact
finite tasks before launch. Allow one one-thread worker, a ten-minute
cooperative ceiling and separately qualified task-level recovery. Save all
matched-epoch rows and failures. Audit and publish without recomputing a fit.
