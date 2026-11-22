# What the receiver exports say about their own precision

The [fixed-window precision audit](PARALLEL_GNSS_REPORTED_PRECISION_PLAN.md)
compares each parallel GNSS-only position export with `air1` during the same
195 fast, two-minute windows selected earlier from receiver speed. It uses
23,399 matched positions per export. Seven focused tests pass. The
[complete result](parallel-gnss-reported-precision-result.json) preserves
the source hashes and per-window differences.

Each number below is an absolute north/east/up position difference divided
by the square root of the **sum of the two exports' reported variances**.
It is a comparison scale, not a statistical significance score: the exports
share an antenna and processing.

| Export against `air1` | Median ratio, N/E/U | 95th percentile, N/E/U | Positions above 3, N/E/U |
|---|---:|---:|---:|
| `mosaic03` | 0.63 / 0.36 / 0.43 | 3.11 / 1.19 / 1.17 | 5.9% / 2.2% / 0% |
| `pwrpak7` | 0.24 / 0.59 / 0.40 | 0.57 / 2.00 / 1.09 | 0% / 0% / 0% |

The `mosaic03` north difference often exceeds the exports' reported
precision scale. The time-window audit also found that most relative error
is a persistent offset within a window, with smaller change across it.
This identifies a receiver consistency issue worth carrying into the
aircraft error model. It does not say which export is correct. Agreement
between shared-antenna exports cannot establish absolute accuracy, and
these ratios do not calibrate withheld prediction coverage or support an
Earth-model decision. No IMU, model fit or reserved ESA flight was used.
