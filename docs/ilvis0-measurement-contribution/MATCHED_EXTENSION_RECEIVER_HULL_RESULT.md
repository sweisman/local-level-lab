# The new forecast rankings survive variation between GPS tracks

On both added flights, the globe retains lower 3D prediction error at both
field settings through 30, 60 and 120 seconds and over the full interval.
The specified-field globe also retains lower 3D error than the zero-field
globe at each horizon. These comparisons allow the shared reference position
to vary independently within the three observed GPS positions at each report.

| Recorder | Worst horizontal RMS for specified-field globe | Worst height RMS | Extra shared displacement needed to tie the full-interval shape comparison, specified / zero field |
|---|---:|---:|---:|
| IMU8 | 8.60 m | 5.13 m | 262 m / 250 m |
| IMU21 | 2.03 m | 6.04 m | 39 m / 76 m |

Only the specified-field globe on each flight meets all four fixed limits
throughout the measured GPS spread. Two short-horizon, height-only
comparisons can tie or change order. Both concern the zero-field shape
comparison on IMU8. All 32 3D comparisons retain their order, including the
relative error between the two disc variants.

The displacement figures describe a sensitivity calculation in the local
GPS metric. The three tracks share satellite observations, so agreement
does not bound errors common to all of them. Both tasks passed, verifying
96 paired ranges and eight accuracy checks. Four focused tests passed.
The study ran no new fits or forecast propagations.

[Fixed method](MATCHED_EXTENSION_RECEIVER_HULL_PLAN.md) ·
[Full results](matched-extension-receiver-hull-result.json) ·
[Reproduction bundle](matched-extension-receiver-hull-evidence/bundle.zip)
