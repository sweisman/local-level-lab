# The IMU forecasts track later horizontal positions more closely

All 40 GPS-only forecasts completed across twenty NASA recording groups
and two forecast cuts per group. A passing IMU forecast was available at
18 of those cuts, across 13 groups. The IMU-based forecast had lower
horizontal error on all 18 comparisons. Height errors favored the IMU
on all nine earlier cuts and four of the nine later cuts.

| Cut | Matched forecasts | Median horizontal RMS, GPS alone | Median horizontal RMS, GPS and IMU | Median height RMS, GPS alone | Median height RMS, GPS and IMU |
| --- | ---: | ---: | ---: | ---: | ---: |
| Earlier | 9 | 99.80 m | 2.09 m | 3.60 m | 0.75 m |
| Later | 9 | 102.70 m | 1.30 m | 4.77 m | 4.43 m |

The fixed GPS-only forecast continued the previous minute's estimated
course and speed along a sphere. None of the 40 GPS-only forecasts met
the transfer study's fixed accuracy screen, compared with all 18 of
the available matched IMU forecasts. The 22 cuts without a passing IMU
forecast remain in the study. Their GPS-only results are available, and
the comparison makes no claim about their relative errors.

The comparison shows how much the complete IMU-based procedure improved
horizontal forecasts on these matched cuts relative to this GPS-only rule.
The contributions of the gyroscope, accelerometer and motion model remain
entangled. Five groups appear in both matched rows.
The recordings come from the same archive and the accuracy screen has not
been calibrated on independent flights.

The first freeze stopped at the accounting call before forecasting. The
corrected freeze used byte-identical measurement inputs and finished all
40 tasks. No inertial fits or original-file reads were added.

[Original comparison plan](REMAINING_GPS_BASELINE_PLAN.md) ·
[Accounting correction](REMAINING_GPS_BASELINE_V2_PLAN.md) ·
[Scores and matching identities](remaining-gps-baseline.json) ·
[Sealed results](remaining-gps-baseline-v2-evidence/replay.zip) ·
[Sealed accounting failure](remaining-gps-baseline-v1-evidence/replay.zip)
