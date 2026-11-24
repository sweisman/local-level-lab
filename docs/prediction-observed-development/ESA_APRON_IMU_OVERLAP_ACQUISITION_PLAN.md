# Locate raw GPS observations during the Nuuk stop with inertial coverage

The earlier [parked-aircraft check](ESA_APRON_NKAR_RESULT.md) precedes
the available inertial measurement unit samples. Freeze GPS seconds
385020 through 385140 on the same receiver-selected Nuuk stop.
This starts two minutes after the first full minute of the
[saved iMAR overlap](ESA_GIRAFE_GROUND_TIES_RESULT.md). The time rule
uses no carrier residuals.

Use the same AIR1 original, archive certificate and standard private
authentication as the [earlier receiver excerpt](ESA_RINEX_WINDOW_RESULT.md).
Start with one 256 KiB probe at byte 15,100,000. Use its timestamp
markers and the previous verified byte-to-time bounds to locate the
target. Allow at most six 256 KiB location probes and three contiguous
1 MiB ranges with 128-byte overlaps. Each request has a 45-second cap.
Reject prefix echoes, short delivery, changed overlaps and incomplete
epochs. Preserve incomplete transfers and their attempts. Use no
reserved groups.

Retain complete half-second records and a following epoch marker.
Record the source, size and hash of every accepted range, and verify the
time coverage before computing any range residuals. A later comparison
needs its own freeze for the common GPS signals and motion checks.

## Confirmed transfer offsets

The first request stopped before any delivery because the server
reported the size of the entire original. The second request used a
bounded transfer with an explicit restart at byte 15,100,000. It
returned 256 KiB containing GPS epochs 384957 through 384979. The
server timed out on the final control reply after delivering the
requested bytes.

Read two 1 MiB blocks starting at bytes 15,750,000 and 16,798,448.
These offsets bracket the selected interval on the observed local
byte-to-time slope. Accept the requested bytes if the final control
reply times out only when both full blocks arrive, neither echoes the
prefix, the 128 shared bytes match and all required GPS epochs pass
the original framing and time checks. Keep the transport outcome
alongside the accepted byte hashes.
