# The two added NASA recordings passed both timing checks

Every original receiver report matched both reconstructed GPS tracks at the
same millisecond. One extra IMU8 GPS epoch lay outside the original window.
The original windows and their two-thirds training split stayed fixed.

| Recorder | Selected inertial packets | Earlier GPS reports | Later GPS reports | Smallest timing margin after allowing ±0.15 seconds |
|---|---:|---:|---:|---:|
| IMU8 | 117,080 | 390 | 195 | 0.266 s |
| IMU21 | 107,478 | 358 | 180 | 0.043 s |

Each file passed the original hash, packet, installation and conversion
checks. The lower timing margin considers both the nominal 200 Hz clock
and the recorded elapsed clock. The inputs preserve all six original
integers per packet and keep later receiver positions in a separate file.
Both tasks passed in 14 seconds. Seven focused software checks passed.
This step prepared data and ran zero model fits.

[Frozen packet plan](MATCHED_EXTENSION_INPUTS_PLAN.md) ·
[Verified input receipt](matched-extension-inputs-receipt.json) ·
[Reproduction bundle](matched-extension-inputs-evidence/bundle.zip) ·
[Matched forecast plan](MATCHED_EXTENSION_FORECAST_PLAN.md)
