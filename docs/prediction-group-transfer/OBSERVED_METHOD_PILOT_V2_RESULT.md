# Observed optimizer comparison

24/24 planned recorded-data fits were preserved. 7/24 passed their new numerical stopping checks; 0 had technical errors. 4/6 matched recording/cut sets met the declared development agreement scales. Stops by method: custom trust-region 3/12; SciPy TRF 4/12.

| Recording ID | Cut | Stops | Largest later-path spread | Training cost range |
|---|---|---:|---:|---:|
| 7df21c836bec5751f83c0cce | inner | 1/4 | 0.752 m | 0.000159 |
| 7df21c836bec5751f83c0cce | outer | 4/4 | 1.24e-05 m | 2.02e-09 |
| 2791235ca0b11b1ef4386e21 | inner | 0/4 | 0.0459 m | 8.07e-05 |
| 2791235ca0b11b1ef4386e21 | outer | 1/4 | 0.000747 m | 1.65e-06 |
| 50f24131843071ae9312c082 | inner | 1/4 | 0.32 m | 0.000214 |
| 50f24131843071ae9312c082 | outer | 0/4 | 0.0559 m | 0.000313 |

The 17 nonstopping fits: 15 failed fresh position stability, 2 failed fresh stationarity. These are numerical stopping outcomes, not evidence for or against an Earth model.

The three selected development stretches span a northern and two southern routes. Their source, duration, latitude and speed are preserved in the saved report and original selection ledger.

| Recording | Duration | Mean latitude | Ground speed |
|---|---:|---:|---:|
| ILVIS0_applanix_55295_20100409_610_LVIS_09Apr10.013 | 4.1 min | 71.9° | 842 km/h |
| ILVIS0_applanix_55846_610_LVIS.013 | 7.4 min | -56.7° | 822 km/h |
| ILVIS0_applanix_57315_610_DMS_20Oct15DMS.013 | 9.2 min | -61.2° | 754 km/h |

The two methods fit identical earlier receiver observations to the recorded IMU increments. Later receiver positions were opened only after each continuous forecast was saved. This is a numerical method diagnostic for one specified-field globe candidate, not a globe/flat comparison or a calibrated aircraft detection. A 0.1 m path spread and 0.01 cost range are development scales, not acceptance thresholds. The original 80-fit study and its 50 nonpassing labels remain intact; 12 sealed original starts were compared without reclassification.

[All new fit outcomes](observed-method-v2-tasks.csv) · [Frozen plan](OBSERVED_METHOD_PILOT_V2_PLAN.md) · [Source selection](remaining-groups.csv) · [Why the method did not qualify](OBSERVED_METHOD_V2_DIAGNOSIS.md)
