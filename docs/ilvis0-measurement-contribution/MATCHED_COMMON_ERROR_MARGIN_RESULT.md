# Forecast accuracy is more sensitive than model ranking to shared GPS error

On the three NASA flights with complete matched forecasts, an additional
shared GPS displacement of **1.69–8.22 m per report** could bring the
preferred forecast to the 10 m horizontal RMS limit. The three model
rankings would need **39.01–62.74 m per report** to reach their first tie.
The values are calculated from fixed forecasts over each full withheld
interval.

| Flight | First tie among the two shape rankings and globe field ranking | First accuracy limit for the specified-field globe |
| --- | ---: | ---: |
| Original IMU8 | Incomplete comparison | Already outside the horizontal RMS limit |
| Added IMU8 | 62.74 m | 1.69 m |
| Original IMU21 | 49.94 m | 7.99 m |
| Added IMU21 | 39.01 m | 8.22 m |

At each report, the reference can move within the spread of the three GPS
solutions and then move by the additional radius. The same displaced
reference is used for all model scores. The error direction can change
from one report to the next. The result describes the size of an allowed
error that could change the reported checks. Actual shared receiver error
and independent-flight accuracy remain open.

The fourth flight still lacks a zero-field disc forecast. The available
specified-field shape comparison would need about 160.46 m of extra
displacement per report to tie. The specified-field globe already misses
the horizontal RMS limit on that flight. Its group decision remains open.

All four tasks completed, using 29 calculations and zero new fits,
propagations or original measurement reads. Eight ranking margins
reproduced the earlier two-flight results. Four focused tests passed.
[Frozen method](MATCHED_COMMON_ERROR_MARGIN_PLAN.md) ·
[All model scores, margins and original dispositions](matched-common-error-margin-result.json)
