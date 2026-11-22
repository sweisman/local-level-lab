# Parallel GNSS exports for the opened ESA flight

The saved ESA FTPS listing for recording 187 contains three GNSS PPP exports:
the already verified `air1` 2 Hz file, a `mosaic03` 5 Hz file, and a `pwrpak7`
1 Hz file. This development check acquires **only** the latter two. Their
names suggest different receiver streams. The [campaign paper](https://essd.copernicus.org/articles/17/1667/2025/essd-17-1667-2025.html)
identifies three separate GNSS receivers connected to one shared aircraft
antenna. The exact `air1` hardware mapping and independence of the PPP
processing remain unverified.

The saved listing SHA-256 is
`31a243814ab7ecd57f79617ae174c21040bcfaadf782cf13680cee2ed85251f1`.
Expected names and byte sizes are `187_mosaic03_ppp_5Hz_final.txt` (54,289,492)
and `187_pwrpak7_ppp_1Hz_final.txt` (10,770,706). Acquire from the established
implicit-TLS FTPS account with the previously pinned server certificate and
private dataset credential file. Never display credentials. Use one exclusive
lock per target, an append-safe partial file, bounded retries, a size check,
SHA-256 receipt and atomic completion rename. A rerun verifies completed
receipts and resumes unfinished partials; it never overwrites an original.

After acquisition, verify text layout, coordinate/time ordering, reported
covariance fields, coverage and overlap with the already sealed **first 400**
development GNSS times. Do not examine the later 120 held-out reports, fit an
Earth model, or open any of the seven protected ESA groups. Match by actual
GPS times within a fixed 2 ms tolerance, without interpolation. A missing
match remains missing; require at least 300 of the 400 training times for a
paired summary. Compare each stream's earlier
positions and velocities against `air1` on common epochs, keeping both raw
values and source hashes. After the first raw comparison, report an upper
bound on apparent displacement from each matched timestamp difference using
the larger reported horizontal speed at that epoch; do not subtract it or
select matches by position difference. Determine from the survey report whether the
exports use separate physical receivers and whether they share processing.

Agreement between parallel PPP exports would not establish absolute accuracy
or independence by itself. Disagreement can place a lower bound on at least
one stream's error, while shared processing and common aircraft motion can
remain. The result may narrow the receiver-error component of the prediction
gate but cannot qualify the complete IMU/motion/receiver error envelope alone.
