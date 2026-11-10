# Primary-receiver precision inventory

## Question

Do the preserved primary GNSS receiver streams contain usable, checksummed
position-precision reports that can inform the separate receiver-error study?
This is a receiver-data inventory, not an Earth-model comparison or a validation
of reported precision against true position error.

## Selection and limits

- The cohort is the existing 53 selected NASA recording files, fixed by the
  saved stretch ledger before any receiver-precision results are inspected.
  The first development check uses recording `a0534d9c30195543709c` because
  its receiver stream was already used for the training-prefix assessment.
- Fifteen files have a preserved `primary-gps-stream.bin.gz`; the other 38 do
  not. Make one strict, hash-checked pass through each retained `.013.gz`
  original to copy Group 10001 payloads only. Check that the 15 existing
  streams match exactly, and stage derived streams for the other 38. The pass
  verifies outer frames but does not decode Group 4 IMU measurements or Group 1
  fused navigation. Record the original-read count, source hash and
  extracted-stream hash. The inventory tasks then use only frozen receiver
  streams, including their NMEA GGA messages. For the 15 previously decoded
  files, compare those messages with saved GGA positions. Do not read model
  residuals, later prediction results or reserved ESA groups.
- One pass per recording, at most 53 tasks, one worker and one thread. No
  optimizer starts, physical integrations, native calls, or Earth-model fits.
  Any separate software qualification has its own finite test run.
- Keep source and input hashes, receiver type, complete checked-packet counts,
  rejected interior spans, boundary-fragment byte counts/hashes, and every
  decoder failure. An interior framing/checksum failure makes that stream
  unavailable for scientific receiver-precision use; do not resynchronize.

## Decoder and checks

Extend the existing Trimble TSIP/RT27 decoder for checked 0x57 subtype 7
enhanced-position records. Validate page numbering and checksum through the
existing framing code; require documented block lengths, GPS week/time range,
finite coordinates, and nonnegative reported sigmas. Preserve raw integer
fields alongside converted positions, velocities and north/east/up sigmas.
Report unknown optional blocks without guessing their meaning.

The saved receiver stream can begin or end inside a packet because Group 10001
logging starts and stops midstream. A bounded boundary scan may remove only
the initial incomplete fragment and terminal incomplete fragment, recording
their exact sizes and hashes. Any failure between complete packets is a hard
failure. Match decoded position epochs to receiver GGA fixes using an
explicit GPS-to-UTC offset and a fixed time tolerance; compare position values
without adjusting them to match. Require at least 100 same-receiver matches
per recording, a 20 ms time tolerance, and a maximum 0.05 m difference on
each coordinate. The predeclared GPS-minus-UTC offsets are 15 seconds from
2009, 16 from July 2012, 17 from July 2015 and 18 from January 2017,
following the [USNO time-scale record](https://www.cnmoc.usff.navy.mil/Our-Commands/United-States-Naval-Observatory/Precise-Time-Department/Global-Positioning-System/GPS-Timing-Data-and-Information/).

First qualify the parser on generated complete/malformed packets and the
preselected development stream. Then freeze the exact adapter, inputs,
environment and allowance before the 53-file inventory. Preserve the earlier
metadata audit unchanged as a historical NMEA-only result.

## Interpretation

The receiver's reported one-sigma fields describe its own position solution.
They are not independent proof of actual GNSS accuracy or temporal covariance.
No Earth-model decision or aircraft prediction-error coverage follows from
their presence. Later work must check calibration and dependence against
independent observations.

Sources: [Applanix receiver type table](https://asapdata.arc.nasa.gov/share/ASF_Applanix/POSv6_User_ICD.pdf),
[Trimble packet framing](https://receiverhelp.trimble.com/oem-gnss/api-data-collector-format-packet-structure.html),
[0x57 paging](https://receiverhelp.trimble.com/oem-gnss/icd-pkt-response57h-rawdata.html),
and [enhanced-position fields](https://receiverhelp.trimble.com/oem-gnss/icd-subtype7-enhanced-position-record-29.html).
