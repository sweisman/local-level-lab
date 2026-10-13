# Updated airborne findings

**15 globe preferences, zero flat, 38 unresolved** among the same 53 preselected stretches. The original study supplied 12 complete comparisons; the qualified recovery adds three. All fifteen favor the specified background-field globe over the zero-field globe in both processing cases. This does not identify the field's physical cause or measure a solar-versus-sidereal difference.

These are numerical model preferences. Statistical significance and uncertainty remain uncalibrated. The original observations, selected intervals and first-pass results are preserved.

## The three newly completed stretches

| Source recording | Recorded IMU type | UTC interval | Duration | Minimum / median ground speed |
|---|---:|---|---:|---:|
| `ILVIS0_applanix_55124_Ames_610-20Oct09_20Oct09.013` | 21 | 2009-10-20T13:23:57.047162Z to 2009-10-20T13:34:45Z | 10.80 min | 837.6 / 848.7 km/h |
| `ILVIS0_applanix_55124_Ames_510-20oct09_20Oct09.013` | 8 | 2009-10-20T13:25:32.783556Z to 2009-10-20T13:35:17.822442Z | 9.75 min | 841.4 / 849.1 km/h |
| `ILVIS0_applanix_55128_Ames_610-24Oct09_24Oct09.013` | 21 | 2009-10-24T13:25:59.003646Z to 2009-10-24T13:37:05.003101Z | 11.10 min | 852.0 / 858.1 km/h |

The three stretches add **31.65 minutes** of completed comparisons. One is IMU8 and two are IMU21, so completed findings now include both recorded types. These codes identify instrument/data configurations, not unique unit serial numbers or different experiment protocols. Their conversion scales are checked separately; the selection and physical model comparisons are the same.

The two October 20 recordings overlap in time and must not be counted as two independent flights. The fifteen resolved stretches contain 15 distinct recording hashes across 10 dates, not fifteen established independent replications. [All 53 stretches](STRETCHES.md) list current dispositions, courses and latitudes. [The current inventory](current-stretches.csv) preserves exact sources, hashes, intervals, speeds and result origins.

## What changed in the calculation

The physical models, gyro-offset bounds, receiver weights and integration clock are unchanged. The revised solver checks its final correction with a fresh full-model prediction in metres, rather than rejecting it solely from a local residual approximation. The gradient and objective-change limits remain; predicted movement must be at most 1 mm RMS per axis and 1 cm at any receiver epoch. These are numerical stopping tolerances, not sensor accuracy claims.

The trial passed **24/24 fits**, including 15 primary recoveries, six controls and three predetermined perturbed-start repeats, using 393 native sweeps. Each newly completed stretch has all six model/case fits and a passing repeat. Repeat agreement demonstrates numerical repeatability under these starts; it does not prove a global minimum. [Individual results](RESULTS.md) and the [finite plan](PLAN.md) retain the evidence.

## Continuing the recovery

The [wider recovery run](../ilvis0-position-recovery-20261013/README.md) is active. It reuses the qualified subset and permits 159 new starts with no retries. Partial fits are not added to the headline until a stretch passes its complete comparison and repeat. Incomplete calculations remain unknown, rather than evidence for either shape.
