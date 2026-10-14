# Updated airborne findings

**30 globe preferences, zero flat, 23 unresolved** among the same 53 preselected stretches. The original study supplied 12 complete comparisons; numerical recovery adds 18, including the three previously recovered in the qualification trial. All thirty favor the specified background-field globe over the zero-field globe in both processing cases. This does not identify the field's physical cause or measure a solar-versus-sidereal difference.

These are numerical model preferences. Statistical significance and uncertainty remain uncalibrated. The original observations, selected intervals and first-pass results are preserved.

## The eighteen recovered stretches

| Source recording | Recorded IMU type | UTC interval | Duration | Minimum / median ground speed |
|---|---:|---|---:|---:|
| `ILVIS0_applanix_55124_Ames_610-20Oct09_20Oct09.013` | 21 | 2009-10-20T13:23:57.047162Z to 2009-10-20T13:34:45Z | 10.80 min | 837.6 / 848.7 km/h |
| `ILVIS0_applanix_55124_Ames_510-20oct09_20Oct09.013` | 8 | 2009-10-20T13:25:32.783556Z to 2009-10-20T13:35:17.822442Z | 9.75 min | 841.4 / 849.1 km/h |
| `ILVIS0_applanix_55128_Ames_610-24Oct09_24Oct09.013` | 21 | 2009-10-24T13:25:59.003646Z to 2009-10-24T13:37:05.003101Z | 11.10 min | 852.0 / 858.1 km/h |
| `ILVIS0_applanix_55129_610-25Oct09_25Oct09.013` | 21 | 2009-10-25T14:57:57.272991Z to 2009-10-25T15:08:45.272659Z | 10.80 min | 839.8 / 843.1 km/h |
| `ILVIS0_applanix_55284_20100329_610_AMES_29Mar100329_103936.013` | 21 | 2010-03-29T13:06:37.134207Z to 2010-03-29T13:13:30.134487Z | 6.88 min | 862.3 / 863.2 km/h |
| `ILVIS0_applanix_55842_610_LVIS.013` | 21 | 2011-10-08T15:00:19Z to 2011-10-08T15:07:25Z | 7.10 min | 891.4 / 904.5 km/h |
| `ILVIS0_applanix_55846_610_LVIS.013` | 21 | 2011-10-12T12:05:40Z to 2011-10-12T12:13:02Z | 7.37 min | 809.3 / 822.5 km/h |
| `ILVIS0_applanix_57289_610_LVIS_38614965.013` | 21 | 2015-09-24T12:47:53Z to 2015-09-24T12:55:12Z | 7.32 min | 788.8 / 793.6 km/h |
| `ILVIS0_applanix_57298_610_loaner_03Oct15LVIS.013` | 21 | 2015-10-03T14:18:15Z to 2015-10-03T14:27:08Z | 8.88 min | 881.4 / 895.6 km/h |
| `ILVIS0_applanix_57305_610_LVIS_38614965.013` | 21 | 2015-10-10T13:51:59Z to 2015-10-10T13:59:04Z | 7.08 min | 816.6 / 823.4 km/h |
| `ILVIS0_applanix_57307_610_loaner_12Oct15LVIS.013` | 21 | 2015-10-12T13:15:12Z to 2015-10-12T13:23:47Z | 8.58 min | 820.4 / 828.4 km/h |
| `ILVIS0_applanix_57307_610_DMS_12Oct15DMS.013` | 21 | 2015-10-12T13:26:58.778403Z to 2015-10-12T13:30:59Z | 4.00 min | 786.5 / 795.9 km/h |
| `ILVIS0_applanix_57312_610_loaner_17Oct15LVIS.013` | 21 | 2015-10-17T13:17:05Z to 2015-10-17T13:25:56Z | 8.85 min | 775.6 / 779.1 km/h |
| `ILVIS0_applanix_57315_610_LVIS_38614965.013` | 21 | 2015-10-20T12:54:29Z to 2015-10-20T13:01:44Z | 7.25 min | 752.0 / 761.1 km/h |
| `ILVIS0_applanix_57315_610_loaner_20Oct15LVIS.013` | 21 | 2015-10-20T13:15:17Z to 2015-10-20T13:24:12Z | 8.92 min | 746.7 / 754.1 km/h |
| `ILVIS0_applanix_57322_610_LVIS_38614965.013` | 21 | 2015-10-27T14:02:23Z to 2015-10-27T14:06:53.480000Z | 4.51 min | 833.8 / 842.8 km/h |
| `ILVIS0_applanix_57324_610_loaner_29Oct15LVIS.013` | 21 | 2015-10-29T13:11:09.888451Z to 2015-10-29T13:20:04Z | 8.90 min | 883.6 / 892.4 km/h |
| `ILVIS0_applanix_57324_610_DMS_29Oct15DMS.013` | 21 | 2015-10-29T13:16:56Z to 2015-10-29T13:26:08Z | 9.20 min | 868.4 / 879.9 km/h |

The eighteen stretches add **147.30 minutes** of completed comparisons. Completed findings include 1 IMU8 and 29 IMU21 stretches. These codes identify instrument/data configurations, not unique unit serial numbers or different experiment protocols. Their conversion scales are checked separately; the selection and physical model comparisons are the same.

The two October 20 recordings overlap in time and must not be counted as two independent flights. The thirty resolved stretches contain 30 distinct recording hashes across 19 dates, not thirty established independent replications. [All 53 stretches](STRETCHES.md) list current dispositions, courses and latitudes. [The current inventory](current-stretches.csv) preserves exact sources, hashes, intervals, speeds and result origins.

## What changed in the calculation

The physical models, gyro-offset bounds, receiver weights and integration clock are unchanged. The revised solver checks its final correction with a fresh full-model prediction in metres, rather than rejecting it solely from a local residual approximation. The gradient and objective-change limits remain; predicted movement must be at most 1 mm RMS per axis and 1 cm at any receiver epoch. These are numerical stopping tolerances, not sensor accuracy claims.

The trial passed **24/24 fits**, including 15 primary recoveries, six controls and three predetermined perturbed-start repeats, using 393 native sweeps. Each newly completed stretch has all six model/case fits and a passing repeat. Repeat agreement demonstrates numerical repeatability under these starts; it does not prove a global minimum. [Individual results](RESULTS.md) and the [finite plan](PLAN.md) retain the evidence.

## Completed wider recovery and remaining failures

The [wider recovery](../ilvis0-position-recovery-20261013/README.md) completed all 159 new starts and 22,355 native integration sweeps, with 117 passing fits: 84/115 primary recoveries, 27/38 repeats and all six controls. There were no execution errors. The combined tally improves from 15/0/38 after the subset to 30/0/23. Some primary and repeat checks failed, so the entire run did not qualify every comparison; only individually complete comparisons contribute to the findings. Incomplete calculations remain unknown, rather than evidence for either shape.

The next investigation compares overlapping flight legs whose instruments have different numerical completion outcomes. [All stretch metadata](ANALYTICS.md) retains last costs, stopping reasons and recorder-pair differences. No recorded interval or physical bound was changed to obtain these recoveries.
