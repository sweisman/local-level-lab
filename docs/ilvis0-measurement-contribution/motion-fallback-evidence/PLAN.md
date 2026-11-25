# Alternative flight controls for aircraft motion

Two IceBridge flights can be checked with the inertial recordings already
on hand. Both have simultaneous recordings from two instruments and at
least four minutes of common support. The public camera catalog provides
a way to pursue a separate motion check on the same flights.

| Flight and saved leg | Common inertial interval, UTC | Cataloged imagery during the interval |
| --- | --- | --- |
| 20 Oct 2015, `leg-8e6717c0a5a0` | 13:17:24–13:24:12, 408 s | 136 DMS images, from 13:17:25.490 to 13:24:10.490. [Catalog query](https://cmr.earthdata.nasa.gov/search/granules.umm_json?short_name=IODMS1B&temporal=2015-10-20T13%3A17%3A24Z%2C2015-10-20T13%3A24%3A12Z&page_size=1) |
| 27 Oct 2015, `leg-b8eb186f98a8` | 14:27:23–14:34:30, 427 s | 40 LVIS images every four seconds, from 14:27:26 to 14:30:02. [Catalog query](https://cmr.earthdata.nasa.gov/search/granules.umm_json?short_name=IOLVIS1A&temporal=2015-10-27T14%3A27%3A23Z%2C2015-10-27T14%3A34%3A30Z&page_size=1) |

These were the only matches when the LVIS and DMS timed catalogs were
checked against all ten same-track overlaps of at least four minutes.
Both selected pairs use separate IMU21 streams. The four retained originals
matched their uncompressed SHA-256 hashes in the flight inventory. Selection
used the saved overlap times and camera metadata. [Pair inventory](../ilvis0-current-findings-20261015/shared-leg-pairs.csv) ·
[Original recording hashes](../ilvis0-current-findings-20261015/current-stretches.csv)

## The control using available data

Run the existing whole-packet alignment on these two additional pairs at
quarter-second and one-second resolution under both packet clocks. Use the
first half of each overlap to choose a relative mounting rotation, rate
offset and shift from the existing ±300 ms grid. Freeze these choices and
measure disagreement on the second half, including unshifted and shifted
scores. Keep both clocks and every available comparison. Use two tasks,
one worker and one numerical thread, with 494 charged operations and at
most 300,000 timed packets per task. Use a 180-second cooperative wall-clock
allowance. No Earth-model fits or reserved ESA reads are needed.
[Existing timing method and earlier controls](PAIRED_GYRO_CLOCK_RESULT.md)

This tests whether disagreement between recorders transfers across flights
and timescales. Both instruments can share aircraft motion or a common error.
An independent upper bound on actual aircraft motion still needs another
observational source.

## An optical check if usable source images are available

The 20 October DMS frames cover almost the entire overlap. Their cataloged
Level-1B imagery has already been orthorectified using navigation data. Use
the catalog only to locate exposures and seek corresponding original camera
frames for independent motion estimation. The raw DMS catalog returned
zero hits for that day. [DMS processing guide](https://nsidc.org/sites/default/files/iodms1b-v001-userguide_1.pdf)

The 27 October catalog links to original camera frames and public reduced
previews. The first four previews downloaded successfully. One inspected
preview has a rotated image border and little stable scene detail. A
quantitative camera check needs original-frame geometry and overlapping
stable features. Estimate relative rotation from the image pixels, validate
the method on known rotations, and check that enough independent features
remain after accounting for translation and scene geometry. Use the archive
timestamps to match exposures. Camera tags for pitch, roll and heading
come from navigation data and are excluded from the independent estimate.
The available image cadence leaves motion between exposures unresolved.
[LVIS imagery guide](https://nsidc.org/sites/default/files/iolvis1a-v001-userguide_1.pdf)

This plan runs separately from RF04 and leaves the ESA error limits and
reserved flights under their existing rules.
