# Check the GIRAFE platform log before matching inertial measurements

The [platform inventory](../external-imu-data/ESA_GIRAFE_187.md) identifies
an additional set of motion measurements on the opened flight. Its first
212 complete rows have a fixed width and a printed clock consistent with
1,024 samples per second. The first log's live size agrees with the
campaign listing. Check whether the same readable row layout continues
inside this 1,860,304,779-byte file.

Use the saved 16,384-byte prefix as the start reference. Attempt three
authenticated reads from the first platform log only. Choose the rows
nearest one quarter, one half and three quarters of its byte length by
rounding each offset down to a 77-byte boundary. Allow exactly 128 rows
per read, a total of 29,568 newly transferred bytes. Check the server's
source size, the requested restart offset and the trusted certificate.
Keep the transferred bytes locally and record their hashes. Preserve each
failed read or invalid block and its charged attempt.

Verify seven finite numeric columns, fixed line endings and chronological
time tags. Test whether each block separately and all blocks together
allow a uniform 1,024 Hz clock rounded to four decimals. If the local
clock fits while the file-wide formula fails, record the phase offsets
and use the times themselves when seeking further samples. No interpolation,
axis conversion or background-field comparison is part of this check.
The channel meanings, units and alignment with the other instruments still
need independent checks before using these data to score directions.

Freeze three byte-range operations, 150 seconds and one numerical thread.
Record the source layout and the acquisition checks without archiving
credentials. The scope is the opened recording 187. No reserved group,
full-file download or navigation fit is required.
