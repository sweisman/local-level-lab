# Verify the FTP restart offset before retaining a receiver excerpt

The [initial byte-range plan](ESA_RINEX_WINDOW_PLAN.md) located the correct
file and header. The first nonzero-range request failed inside the sandbox
at DNS. The next request wrote 256 KiB and timed out. Those bytes matched
the offset-zero prefix exactly, so the proposed offset was rejected.

A separate probe explicitly sent the FTP binary transfer and restart
commands. It returned a different 256 KiB slice whose timestamp markers
bracket the target. Verify its saved hash and reuse it to locate the
starting byte. Require success, exact lengths and agreement across
128-byte overlaps for all following requests. Preserve both failed
attempts and give the corrected transfer its own freeze and directory.

Keep the original GPS interval and read limits. Use at most nine 1 MiB
requests for the retained window and its end marker, with at most three
attempts per request. Inspect the 520 existing query times without opening
their later positions. Verify all half-second epochs and their satellite
counts. No position solutions or new model fits are part of this preflight.
