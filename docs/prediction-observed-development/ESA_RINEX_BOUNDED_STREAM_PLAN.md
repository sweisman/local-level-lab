# Read a verified prefix of each restarted FTP data stream

The [explicit restart transfer](ESA_RINEX_REST_PLAN.md) received the full
first 1 MiB range and reproduced the starting overlap. The FTP server
did not finish its control reply after the client stopped the transfer
at the planned limit. The incomplete protocol attempt stays in its
original directory.

Use the same certificate, source size, byte starts, query times, per-range
cap and overlap check. Verify the FTP restart acknowledgement, then read
exactly the requested bytes on the authenticated data connection. Close
each connection at that boundary. A short read, timeout during delivery,
incorrect source size, missing overlap or incomplete observation epoch
fails the check. The last accepted epoch still requires a following
marker to verify its completeness. The initial 1 MiB is also checked
against the preserved bytes from the preceding attempt.

Keep a separate transport freeze. The original scientific acceptance
conditions, reserved-group restrictions and finite byte limits still apply.
