# Matched forecasts and absolute accuracy by NASA flight group

Across four preselected NASA flight groups, 15 of 16 fits produced scorable
forecasts. With the specified field held fixed, the globe gave lower 3D
position error on all four flights. With the field set to zero, it gave
lower 3D error on all three flights with a complete pair. All three then
favored the specified field over zero in the globe comparison.

| Flight group | Scorable fits | Shape at specified field | Shape at zero field | Globe field | Meets all four accuracy limits on all three GPS tracks |
|---|---:|---|---|---|---|
| Original IMU8, 11.13 min | 3/4 | Globe | Unresolved | Unresolved | None |
| Added IMU8, 9.75 min | 4/4 | Globe | Globe | Specified | Specified-field globe |
| Original IMU21, 7.37 min | 4/4 | Globe | Globe | Specified | Specified-field globe |
| Added IMU21, 8.95 min | 4/4 | Globe | Globe | Specified | Specified-field globe |

The original IMU8 zero-field disc fit exhausted its allowance. The same
flight's specified-field globe had lower 3D error than its matched disc,
but its horizontal RMS exceeded 10 m. The other three specified-field
globe forecasts met all four limits on all three GPS tracks. These tracks
share measurements and satellite data within each flight. The four flights
are retrospective development cases from southern latitudes. Aircraft
coverage remains uncalibrated.

The [eight added fits](MATCHED_EXTENSION_FORECAST_RESULT.md) all passed.
The saved-data audit independently rebuilt the training prefix and later
errors and verified charges. It ran zero new fits or propagations.

[Fixed method and replay command](MATCHED_FOUR_GROUP_AUDIT_PLAN.md) ·
[All fit dispositions, errors and 30-second summaries](matched-four-group-audit.json)
