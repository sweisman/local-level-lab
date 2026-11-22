# Receiver quality across the opened ESA recording

The [fixed receiver-only audit](FULL_RECEIVER_CONSISTENCY_PLAN.md) checked all
**64,080** reports in the already opened ESA development flight. It used the
original GNSS-only PPP export, divided in advance into eight consecutive
windows of 8,010 reports each. No IMU, model fit or protected flight was read.

| Window | Median ground speed | Median reported north/east/height position SD | Position-derivative minus reported-velocity RMS, north/east/height |
| --- | ---: | ---: | ---: |
| 1 | 0 km/h | 3.0 / 2.3 / 5.4 cm | 1.27 / 1.62 / 1.87 cm/s |
| 2 | 336 km/h | 2.9 / 1.9 / 4.6 cm | 1.61 / 0.89 / 3.30 cm/s |
| 3 | 310 km/h | 2.7 / 1.8 / 5.4 cm | 1.25 / 0.57 / 1.98 cm/s |
| 4 | 303 km/h | 3.0 / 2.1 / 5.6 cm | 1.20 / 0.69 / 1.99 cm/s |
| 5 | 290 km/h | 2.2 / 2.0 / 5.6 cm | 1.01 / 0.66 / 1.97 cm/s |
| 6 | 274 km/h | 2.9 / 2.1 / 5.1 cm | 1.27 / 0.88 / 2.45 cm/s |
| 7 | 262 km/h | 2.5 / 2.0 / 5.6 cm | 1.09 / 0.78 / 2.36 cm/s |
| 8 | 260 km/h | 2.6 / 2.0 / 5.5 cm | 1.37 / 1.23 / 3.75 cm/s |

All 64,080 printed position covariance matrices and all printed velocity
covariance matrices are positive semidefinite under the audit tolerance.
Reported precision varies modestly across the flight; the internal
position/velocity disagreement is also fairly stable. Window 1 contains much
ground time, while later windows are moving. A separate ground-interval check
can examine receiver drift where actual aircraft motion is small.

These numbers do **not** establish centimetre-level true position accuracy.
Position and velocity come from the same PPP solution, and the export lacks
cross-time covariance and an independent position truth. Consequently this
audit does not qualify the working receiver law, the IMU error law, prediction
coverage or an Earth-model decision. The [saved numerical report](full-receiver-consistency-result.json)
contains the eight window boundaries, source and code hashes, covariance
checks, route summaries and lag correlations. Five focused tests passed.
