# Can survey photos independently show aircraft motion?

We checked the exact UTC bounds of all 53 saved NASA stretches against
three image catalogs. Seventeen stretches had timestamp matches. The
checked previews did not show recognizable fixed features to support an
independent motion measurement. No aircraft fits were run.
[All 53 catalog results](camera-catalog-screen.csv) ·
[The saved stretch selection](../ilvis0-current-findings-20261015/current-stretches.csv)

| Catalog | Stretches with time matches | What the product can provide |
| --- | ---: | --- |
| LVIS geotagged imagery, `IOLVIS1A` | 11 across 7 dates | Timed exposures and links to full-size files. Any motion check would need fixed features in successive images and known camera geometry. |
| DMS raw imagery, `IODMS0` | 0 | The search found no raw images cataloged during these intervals. |
| DMS orthorectified imagery, `IODMS1B` | 9 across 6 dates | Exposure times. The image geometry already uses the navigation solution. |

Three stretches matched both LVIS and orthorectified DMS. Matching
timestamps alone cannot establish whether the camera saw a fixed scene
or whether two frames cover the same ground.
[LVIS product guide](https://nsidc.org/data/iolvis1a/versions/1) ·
[DMS raw product guide](https://nsidc.org/data/iodms0/versions/1) ·
[DMS orthorectified product guide](https://nsidc.org/data/iodms1b/versions/1)

For each LVIS match, we checked the middle pair of successive CAM1 frames
and also checked the leading pair for three of the stretches. The 28 public
reduced images mostly showed uniform surfaces, clouds or water. The review
found no clearly identifiable fixed features in both views of a pair. This
was a visual screen of reduced images. Other exposures or full-resolution
files could contain detail the screen missed. Ten middle pairs were spaced
four or five seconds apart, and the remaining pair was 30 seconds apart.
Even usable pairs would leave motion
between exposures unresolved. [Preview URLs and image hashes](camera-preview-screen.csv)

## Reproduce the catalog screen

Use the UTC start and end values for each row as the `temporal` parameter
and the collection short name as `short_name`. Read the `CMR-Hits` response
header. For a positive LVIS query, retrieve the timed entries and sort CAM1
exposures by capture time. The middle pair starts at the zero-based index
`(image_count - 1) // 2`. The input stretch CSV has SHA-256
`7f41d5c4ea5bb8b76c5daf069631bfdf7cd3531ad0e7491147686267c87ac51e`.
[Example query](https://cmr.earthdata.nasa.gov/search/granules.json?short_name=IOLVIS1A&temporal=2015-10-27T14%3A27%3A23Z%2C2015-10-27T14%3A34%3A30Z&page_size=1)

The RF04 stretch had no matches in any of the three catalogs. The later
NASA aircraft-file check found the same one-second observations as NCAR.
[RF04 file comparison](NCAR_RF04_INTAKE.md#what-the-nasa-text-file-adds) ·
[RF04 source audit](MOTION_SOURCE_AUDIT.md)
