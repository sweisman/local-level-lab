# Check the processed GIRAFE clock against the original acceleration log

The [level 1 headers](../external-imu-data/ESA_GIRAFE_187.md) give GPS times
for processed GIRAFE vertical acceleration. Check whether these times label
the same acceleration samples as the original Nuuk–Reykjavík log. A match
could pin down the relative export timestamp. The vertical channel leaves
horizontal quartz timing and aircraft attitude to separate checks.

## Acquisition check

Both requests returned the expected number of bytes. Their bytes matched
the saved file prefix, and the GPS times confirmed that both transfers
began at the start of the recording. The second request timed out
after delivering its byte allowance. Neither file covers its intended
interval, so both are retained as failed acquisition evidence.

| Requested excerpt | Received bytes | GPS seconds of week received | SHA-256 |
| --- | ---: | --- | --- |
| Earlier flight | 55,029 | 384898.51739992–384920.41739992 | `f4aa862c633062128c1b25ee809d09782f468349873edef04b1a62293578768d` |
| Existing carrier score | 328,929 | 384898.51739992–385030.41739992 | `eaef0e070807bad3e37f6ba2b7c02e0da4aa596b6437de05a734fc2e2eb5494e` |

Both planned transfer attempts are accounted for. A follow-up acquisition
needs a verified byte offset and timestamp coverage before the force
comparison can proceed. The comparison has yet to run.

## Planned comparison

Use the existing 8,192-byte GIRAFE prefix and make two range requests to
`/lvl1/accelerations/187a_girafe_accelerations.txt`. The byte positions
assume 249 bytes per row from the prefix, with about six seconds of margin
at either end. Confirm coverage using the actual decoded timestamps.

| Excerpt | GPS seconds of week, half-open | Inclusive byte range |
| --- | --- | --- |
| Start of recording | 384898.5–384901.6 | Saved prefix |
| Earlier flight | 388215–388225 | 8243145–8298173 |
| Existing carrier score | 388614–388734 | 9236655–9565583 |

Allow one request per range with a 60-second limit and 383,958 new bytes
in total. Preserve original bytes and hashes. Verify GPS week 2269, 10 Hz
coverage and the GIRAFE column order. Compare the export’s `z-acc` column
with the original vertical acceleration. Convert the original UTC clock
using the known flight-day offset. Report raw-minus-export timestamp and vertical-force
differences to the nearest original sample at each of 41 fixed shifts,
from −2 to +2 seconds in 0.1-second steps. Keep every shift and match by
time without fitting a force offset, reordering or interpolating values.

Report the RMS, mean and maximum absolute force difference and mean and
range of timestamp differences. Call the export consistent with copied
samples only if the same single shift achieves at most 0.000001 m/s² RMS
in all three excerpts. A correlation without agreement in the original
units would leave the time origin unsettled by this comparison.

Use one numerical thread, three excerpts, at most 240,000 original rows
and zero native calls or model fits. Keep all measurements within the
already opened ESA development recording 187. The saved inputs and source
hashes must be verified before executing the comparison.
