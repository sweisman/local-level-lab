# Receiver windows available for the next IMU comparison

The previously selected 53 aircraft stretches contain 52 strictly decoded
primary GPS receiver position streams. Under the [fixed receiver-only window
rule](PLAN.md), **2,194 of 2,365** examined times have usable local windows
(92.8%). Every one of the 52 decoded stretches has at least one. The other
recording retains its earlier decoder failure as an abstention.

| Selected half-window | Target times |
|---|---:|
| 15 seconds | 1,632 |
| 10 seconds | 221 |
| 5 seconds | 341 |
| No accepted window | 171 |

At each of the 171 unsupported times, all three candidate windows exceeded
the declared limit on variation in the receiver's reported vertical velocity.
The limit was fixed before this study ran. This result may inform a separate
future support policy, but this study does not change its own rule.

The [per-stretch table](stretches.csv) records support counts and the preserved
decoder abstention. The [target table](targets.csv) records every candidate
window's rejection reason. The [receipt](receipt.json) hashes both public
tables and the sealed study results. No position gaps were filled, no IMU or
fused navigation observations were used, and no Earth model was fitted.

This establishes where the receiver can supply a local trajectory estimate
under one declared development rule. It does **not** establish the receiver's
actual error distribution, the uncertainty from choosing windows using noisy
receiver data, or what the gyroscope adds. Those are the next gates for a
matched recorded-data comparison.

A [saved-data threshold audit](MARGIN_AUDIT.md) now reports the distance of
each candidate window from the vertical-motion limit. Among 2,194 chosen
windows, 398 sit within 0.10 m/s of that limit. This flags a selection
sensitivity to examine; it is not a measured receiver-error rate.
An [eleven-pair receiver comparison](../ilvis0-receiver-window-pairs/README.md)
then applied the same screen at 490 common target times: the two receivers
agreed on acceptance at 483 and disagreed at seven. It measures relative
repeatability, not absolute window-selection accuracy.
