# The two tracks in the horizontal-only check

These are complete, previously selected stretches. The shorter artifact-complete
stretch from each configuration was chosen before refitting, using duration
rather than model preference. “IMU8” and “IMU21” are recorded Applanix configuration
labels; they do not by themselves identify an individual physical unit.

| Configuration | Duration | Median ground speed | Minimum ground speed | Mean GPS course | Mean latitude |
|---|---:|---:|---:|---:|---:|
| IMU8 | 585.04 s / 9.75 min | 849.11 km/h | 841.40 km/h | 203.69° | 63.07° S |
| IMU21 | 244.00 s / 4.07 min | 841.74 km/h | 834.33 km/h | 86.36° | 71.89° N |

Course is the GPS direction of travel, not measured aircraft heading. A heading
or crab estimate from fused navigation is not an observation in these fits.
The recordings come from distinct dates and geographic regions; this does not
establish every installation's identity or make all stretches in the archive
independent flights.

## IMU8: southern, southwest-going stretch

- Recording: `ILVIS0_applanix_55124_Ames_510-20oct09_20Oct09.013`.
- UTC interval: **2009-10-20 13:25:32.783556–13:35:17.822442**.
- Stretch ID: `b365bdf39150ee6afc303ac1`.
- Original SHA-256: `f39deb582f207574911dd3a16e6c389a8baac76ceace13ec2f13aefdc42341dd`.
- Horizontal-only outcome: all six repeat comparisons pass; globe preferred
  under both processing cases.

## IMU21: northern, east-going stretch

- Recording: `ILVIS0_applanix_55295_20100409_610_LVIS_09Apr10.013`.
- UTC interval: **2010-04-09 12:56:16.115058–13:00:20.115282**.
- Stretch ID: `7df21c836bec5751f83c0cce`.
- Original SHA-256: `b479a9a435e4e89047a18b53ba884364fe487a90b5bad42f8a6a2bb107a72bbd`.
- Horizontal-only outcome: all individual fits pass, but three repeat comparisons
  fail. Both initializations rank specified-field globe first; the matched result
  remains unresolved under the fixed repeatability policy.

Metadata comes from the preserved [all-stretch analytics CSV](../ilvis0-current-findings-20261015/stretch-analytics.csv)
and [original eligibility catalog](../ilvis0-highspeed-segments-20261008/eligible-stretches.csv).
No track or eligibility interval was recalculated for this page.

[Results and limits](INTERPRETATION.md) · [All 53 stretches](../ilvis0-current-findings-20261015/STRETCHES.md).
