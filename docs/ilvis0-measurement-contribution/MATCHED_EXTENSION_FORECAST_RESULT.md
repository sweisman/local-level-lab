# All eight fits on the added NASA flights passed

The globe forecasts had lower 3D prediction error than the matched disc
forecasts on both flights at both field settings. All three GPS tracks
gave those same rankings. After the shape comparisons, the specified-field
globe predicted the later positions more closely than the zero-field globe
on both flights. Only the specified-field globe met all four fixed position
limits on each flight and against each GPS track.

| Recorder | Later GPS reports | Globe, specified field | Disc, specified field | Globe, zero field | Disc, zero field |
|---|---:|---:|---:|---:|---:|
| IMU8, 9.75 min | 195 | 9.31 m | 424.08 m | 96.39 m | 313.45 m |
| IMU21, 8.95 min | 180 | 4.54 m | 64.55 m | 87.28 m | 207.41 m |

The table shows 3D RMS error against onboard GPS. The full report also
provides horizontal and height errors separately. At zero field the
added IMU21 disc has smaller height RMS than the globe, while the globe
has smaller horizontal and 3D errors. Each study model used the same
training-only split and fixed numerical limit.

The eight fits used 109 native calls, including eight forecast calls, and
finished in 19.3 minutes. The saved forecasts passed an independent
replay of their training prefixes, scores and charge counts. These two
groups were chosen before fitting for development and remain part of the
same NASA archive. The accuracy screen is descriptive. Its pass rate has
not been calibrated on independent flights.

The [receiver-spread check](MATCHED_EXTENSION_RECEIVER_HULL_RESULT.md)
retains the 3D rankings and both fixed accuracy passes when the shared
reference can vary between the three observed GPS positions at each report.

[Frozen forecast plan](MATCHED_EXTENSION_FORECAST_PLAN.md) ·
[Four-flight audit](MATCHED_FOUR_GROUP_AUDIT_RESULT.md) ·
[Saved fit and forecast results](matched-extension-forecast-result.json) ·
[Reproduction bundle](matched-extension-forecast-evidence/bundle.zip)
