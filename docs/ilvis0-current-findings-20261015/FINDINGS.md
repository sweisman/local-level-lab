# Updated airborne findings

**47 globe preferences, 0 flat preferences, 6 unresolved** among 53 preselected stretches.

The completed nine-stretch assessment added three complete globe preferences, bringing the tally to 44/0/9. The subsequent hybrid-solver trial resolved two more, and the completed six-target assessment adds one. Every added result passed six primary fits, every required repeat pair and both controls. These are numerical preferences, without a calibrated significance level. All 47 globe-preferred stretches also favor the specified background field; its cause is not determined.

## Latest matched comparison

The six-target hybrid assessment completed all 24 starts using 1,336 native sweeps. Seven fits passed, including both controls, one primary and four repeats. One stretch passes its complete comparison and repeat; five remain unresolved. Passing repeats alone cannot replace failed primaries or another required pair.

The subsequent four-start timing-aware trial used 237 native calls. Both controls passed; the target primary and repeat still failed fresh stability, so the tally is unchanged. That candidate did not qualify for wider use.

| Newly completed source | UTC interval | IMU type | Minutes | Ground speed min / median |
|---|---|---:|---:|---:|
| `ILVIS0_applanix_57289_610_loaner_24Sept15LVIS.013` | 2015-09-24T13:06:34Z to 2015-09-24T13:15:39Z | 21 | 9.08 | 769.8 / 784.8 km/h |

## Six unresolved stretches

All remaining stretches have now been tested with the hybrid solver. Ten primary fits in five assessment targets remain unfinished; one primary in the earlier matched trial also remains unfinished. These failures stop before their evaluation caps when the local solver cannot predict further improvement. Some endpoints fail stationarity, others fail fresh prediction stability. They are numerical failures, not ties between shapes. Native timing checks found changes in the local derivative at a packet boundary. The next focused diagnosis audits the stopping check at such boundaries and screens the other saved endpoints before additional fits. No previous allowance is reopened.

[All stretches and source tracks](STRETCHES.md) · [Comprehensive metadata](ANALYTICS.md)

- [Preserved ilvis0-budget-continuation-20261014 results](../ilvis0-budget-continuation-20261014/RESULTS.md).
- [Preserved ilvis0-remaining-precision-20261014 results](../ilvis0-remaining-precision-20261014/RESULTS.md).
- [Preserved ilvis0-trust-trial-20261015 results](../ilvis0-trust-trial-20261015/RESULTS.md).
- [Preserved ilvis0-hybrid-remaining-20261015 results](../ilvis0-hybrid-remaining-20261015/RESULTS.md).
- [Preserved ilvis0-timing-trial-20261016 results](../ilvis0-timing-trial-20261016/RESULTS.md).

Earlier [41/0/12 findings](../ilvis0-position-stability-trial-20261013/FINDINGS.md) remain an unchanged historical snapshot. No observations, intervals, physical bounds, receiver weights or clocks were changed by this metadata publication.
