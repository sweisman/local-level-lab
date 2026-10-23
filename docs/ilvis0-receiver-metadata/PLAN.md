# Primary-receiver metadata availability

Before choosing a prediction error model, establish which independent receiver
information is already preserved. This audit uses the same 53 preselected
stretches and their saved inspection reports. Group recordings by the existing
task/source identifiers; do not select them using model residuals or convergence.

For each recording, verify its filename and original SHA-256 against the stretch
catalog. Record the primary-receiver type codes from version strings, NMEA text
sentence types and talkers, checksum counts, total stream bytes and bytes not
parsed as NMEA. Preserve missing reports and malformed-record failures.

GST/GBS presence is an availability indicator, not validation of a covariance.
GSA and GGA quality information do not become noise standard deviations.
Unparsed bytes remain unidentified; do not call them raw pseudoranges, receiver
precision or evidence of a particular binary protocol. Receiver type codes do
not establish manufacturer identity or independent physical instruments.

The study reads **no original IMU file**, performs no native prediction or fit,
and uses no fused-navigation covariance or model outcomes. It cannot establish
an aircraft error law or change any model preference.

Freeze the catalog copy, metadata copies, source and environment through the
common study runner. Allow one task per distinct catalog recording, at most
53 tasks and 1 MB per inspection input. Use one worker with one numerical-thread
allocation and a 120-second cooperative clock allowance. Native calls, packet
visits, bound evaluations and optimizer starts are all zero. No retries or
budget expansion.

Recompute the inventory from sealed inputs for publication, preserving every
file outcome. Archive duplicate source/input/evidence copies with verified aliases.
Future checksummed receiver-stream extraction or covariance development require
a separate scope; this audit authorizes neither.
