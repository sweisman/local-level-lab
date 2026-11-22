# Check timestamp support on the reserved ESA groups

Choose the earliest provisional receiver window in each of the seven reserved
groups, ordered by numerical GPS week and second. Check the first 1,200
seconds of that window. This is an integrity check for the earliest slice,
with final confirmation selection still separate. Use only the recorded
timestamp and line framing from the named IMU source.

The source catalogue lists files consistent with 120-byte records. Verify the
documented header and initial timestamp in a 240-byte probe. Use the nominal
300 Hz rate and a five-second guard at either end to locate a fixed-width
byte range for the receiver slice. Clamp the range to the original file.
Require its exact declared byte count. Decode the first field in each record
as GPS seconds of week, preserving every printed fractional digit. Check
that the first and last timestamps bracket the entire receiver slice. Require
strictly increasing time and no gap larger than 1.5 nominal periods within
the slice. Unexpected layouts or insufficient coverage remain unresolved.

Allow one probe and one bounded range per group, with at most 320 MB of
transfers per complete attempt. Use one numerical thread and one timestamp
integrity task per file. Freeze source, evidence, and finite work limits,
and use the repository's tested technical recovery. Retain source sizes,
hashes of exact received ranges and timing summaries. Keep the original
downloaded excerpts local. Publish timestamps or summaries only. No Earth-model
fits or protected model-outcome inspection are part of this check.
