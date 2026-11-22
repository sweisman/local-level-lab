# Match raw observations from the three receivers on ESA flight 187

Use only the already opened 400/120 development window from GPS week 2269.
Acquire exact RINEX observations from GPS seconds 388214 through 388735,
inclusive, from the additional Septentrio and NovAtel files. Retain their
original headers and byte offsets. Verify chronological framing and all
expected 5 Hz and 1 Hz epochs, including the final marker delimiting the
last retained epoch. Use bounded FTPS reads on the two known file paths.
Collect no more than 16 MiB of covering byte ranges for Septentrio and 5 MiB
for NovAtel, with no more than six 256 KiB locating ranges per receiver.
For a byte-range response, check its length and the overlap against a
separate range beginning before the retained data. Preserve both original
inputs and SHA-256 hashes so local analysis can run without the archive.

Compare adjacent integer-second intervals common to all three receivers.
Use only GPS L1C and L2W phase on the same satellite and discard pairs with
missing measurements or loss-of-lock marks. For AIR1 also require both
half-second steps in its archived continuity screen, and omit the interval
crossing its known clock step. Construct ionosphere-free phase changes in
metres for each receiver. For each receiver pair and interval, remove the
median across shared satellites to absorb a common receiver clock change.
Use the same intersection of at least five satellites for all three pair
comparisons and retain omissions and separate
earlier and later statistics. This measures disagreement in carrier tracking
and receiver processing. Shared antenna, propagation and satellite errors
can cancel in this comparison.

Freeze the match rule before evaluating the paired differences. Use one
numerical thread and a 60-second cooperative limit. Charge each of the 519
intervals on the common AIR1 grid once. Preserve all three pair inventories
and their signed per-satellite residuals. No new trajectory fit, reserved
flight, or scientific decision enters this comparison.
