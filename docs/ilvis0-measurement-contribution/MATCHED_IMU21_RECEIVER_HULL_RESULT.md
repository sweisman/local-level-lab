# The IMU21 forecast ordering survives the measured GPS spread

On the completed four-candidate IMU21 recording, the globe has lower
3D and horizontal position error at both matched fields. At zero field,
the disc has lower height error. These orderings hold from the first
30 seconds through the full 148-report forecast, even when the shared
GPS reference is allowed to move anywhere between the three receiver
solutions at every report.

| Matched comparison | Measure and lower-error shape | Extra displacement allowance for a tie, first 30 seconds | Extra allowance, full forecast |
| --- | --- | ---: | ---: |
| Specified field | 3D, globe | 2.84 m | 49.94 m |
| Specified field | Height, globe | 0.83 m | 6.07 m |
| Zero field | 3D, globe | 10.41 m | 84.39 m |
| Zero field | Height, disc | 1.28 m | 6.89 m |

Each allowance is the smallest maximum displacement per report beyond
the measured receiver spread that could produce a tie. Both forecasts
in a comparison are scored against the same perturbed reference. The
table gives sensitivity thresholds. It does not estimate the actual
error common to all three GPS routes.

The field comparison within each geometry also favors the specified
field in 3D at all four horizons. At the full horizon, the corresponding
tie allowances are 99.86 m for the globe and 121.03 m for the disc.
The disc's zero-field forecast still has the lower height error within
that geometry. All these comparisons come from one development recording.

The check verified all four saved forecast identities and the common
later positions. All 48 comparisons finished, with zero new fits.
Four focused tests passed. Independent-flight accuracy and calibrated
uncertainty remain open.

[Frozen method](MATCHED_IMU21_RECEIVER_HULL_PLAN.md) ·
[All comparisons](matched-imu21-receiver-hull-result.json) ·
[Sealed execution](imu21-receiver-hull-evidence/README.md) ·
[Reproduction bundle](imu21-receiver-hull-evidence/bundle.zip)
