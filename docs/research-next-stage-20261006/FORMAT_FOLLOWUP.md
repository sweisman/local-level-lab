# Resolving the airborne gyro format

The initial inspection preserved the supplied Applanix log with timing, GPS and an opaque
24-byte IMU8 payload. On 7 October 2026, a separate numerical validation reproduced its
interpretation as six signed little-endian int32 increments: velocity X/Y/Z and angle X/Y/Z.
Independently estimated scales support `2^-14 m/s/count` and `2^-18 rad/count`, with expected
axis order/signs and chronological holdout checks. Rates use actual adjacent timestamps;
gaps and configuration changes never become silently interpolated observations.

The [validation record](../ilvis0-physical-validation-20261007/README.md) reports the
comparisons against Group-1 fused navigation, including shared body-frame gravity for
accelerometer checks. Group 1 is a decoder reference, not an independent Earth observable.
No authoritative manufacturer scale table has been found. Calibration/corrections, exact
mounting, lever arms and physical latency remain unresolved.

A later [IMU6 installation/clock investigation](../ilvis0-installation-clock-20261007/README.md)
reproduces changed axes from logged legacy setting candidates. Its earlier vertical mismatch
largely disappears when increments are normalized by a fixed 200 Hz period rather than
fluctuating header intervals. All six acceleration checks pass under that explicit hypothesis;
one gyro holdout narrowly fails. This finding is specific to these IMU6 records and does not
replace the IMU8 timestamp convention above. Both rate normalizations and the original
failure reports are preserved. Integration-clock semantics and processing independence
remain unresolved; no automatic corpus conversion is enabled.

The [public Applanix interface document](https://asapdata.arc.nasa.gov/share/ASF_Applanix/POSv6_User_ICD.pdf)
establishes the packet container and directs IMU data to POSPac processing. It does not
provide the needed physical payload definition. The inspected processing instructions describe
navigation processing; a smoothed trajectory export would not supply independent gyro data.

There is a documented format for preserving decoded IMU observations:
[Waypoint IMR](https://docs.novatel.com/Waypoint/Content/Data_Formats/IMR_File.htm).
Its header records byte order, rate/increment conventions, scale factors, sampling rate and
time basis. The [raw converter documentation](https://docs.novatel.com/Waypoint/Content/Inertial_Utilities/Raw_IMU_Data_Converter.htm)
does not establish that this exact Applanix log is supported. A compatible export would still
need its source conversions and corrections documented. No software purchase, installation,
conversion or invented IMR header has been performed.

Instrument type numbers belong to their respective manufacturers' formats. For example,
the [NovAtel type table](https://docs.novatel.com/OEM7/Content/SPAN_Commands/CONNECTIMU.htm)
assigns number 8 to LN200; that does not establish the identity or scaling of Applanix IMU8.
An unrelated type table must not determine this decoder.

The useful external step is now requesting processing, mounting and timing documentation.
The earlier request is preserved in
[AIRBORNE_DATA.md](AIRBORNE_DATA.md). The verified manufacturer
[support page](https://applanix.trimble.com/en/support) lists `techsupport@applanix.com`.
The dataset's [NSIDC page](https://nsidc.org/data/ilvis0/versions/1) is the archive contact
starting point. No inquiry has been sent. Sending one requires explicit user instruction.

Keep original measurements immutable. Additional `.013` logs now help check cross-file
compatibility and discover level-flight windows even while proprietary processing details
remain unknown. Every new configuration must pass its own checks; a result for IMU8 does
not establish another IMU type's scales. Existing fused navigation may describe maneuvers
but must not replace independent gyro evidence. The [acquisition guide](../ILVIS0.md)
describes the streaming decoder, catalog, safe downloader and geometry-only retention policy.
