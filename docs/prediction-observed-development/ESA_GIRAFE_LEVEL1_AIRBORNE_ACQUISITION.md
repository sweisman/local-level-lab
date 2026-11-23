# Acquire the two airborne clock intervals from a bounded prefix

The [two previous requests](ESA_GIRAFE_LEVEL1_CLOCK_PLAN.md) for nonzero
byte offsets both returned the start of the processed GIRAFE export.
Use a single read from the beginning instead. Allow one request for the
first 9,565,584 bytes of
`/lvl1/accelerations/187a_girafe_accelerations.txt` with a 120-second
limit. Use the already trusted ESA endpoint and certificate. Store it
under a new local name and preserve any incomplete response. The original
attempts and their charges stay in their own record.

Check the response against the existing 328,929-byte prefix before
decoding. Record the count, transfer exit status and SHA-256. The
1,320 complete records in the smaller response each occupy 249 bytes.
Use the new records' actual timestamps to verify coverage of GPS seconds
388215–388225 and 388614–388734 in week 2269. The byte estimate supplies
extra space on both sides of each target and assumes the record layout
continues. Reject gaps, changed column layout and missing target times.

The [recording-start check](ESA_GIRAFE_LEVEL1_PREFIX_RESULT.md) established
the sign reversal and zero offset for the vertical values at that end of
the file. Freeze that sign for the later comparison and keep the full
time-shift grid as a diagnostic. Seal the acquired inputs before running
the comparison. Use only the open ESA development recording 187.

## Verified transfer

The saved response contains all 9,565,584 requested bytes and matches
the shorter capture byte for byte over the shared prefix. Its 38,415
processed samples run continuously at 10 Hz from GPS second
384898.51739992 through 388739.91739992. The server's final response
timed out after the requested bytes arrived. Both target intervals and
their timing margins are present.
[Transfer receipt](esa-girafe-level1-airborne-acquisition.json) ·
[Airborne check](ESA_GIRAFE_LEVEL1_AIRBORNE_RESULT.md)
