# Final selected-stretch analysis summary

Of 53 selected stretches, the completed conditional shape comparisons favored globe in 12 and flat in 0. 41 remained unknown; 0 were unsupported.

The shape question comes first. These are conditional comparisons under assumed calibration and processing, not calibrated scientific detections. Overlapping instrument streams are not independent flights.

## Shape and rotation

| Conditional shape outcome | Stretches |
|---|---:|
| Globe | 12 |
| Flat | 0 |
| Unknown: unresolved fits | 41 |
| Unknown: conflicting or tied comparisons | 0 |
| Unsupported | 0 |

Rotation is exposed only for resolved globe stretches. Across their processing cases, 24 favored rotating globe, 0 favored still globe and 0 tied. These are matched case comparisons, not independent votes.

## Which calculations finished?

The following counts measure solver completion, not model support. A flat-disc calculation can finish while describing the flight much worse than a globe. The quality of matched fits determines the comparison; counting finished calculations does not.

188 calculations passed the stopping checks, 130 remained numerically unresolved and 0 returned an explicit error. 318 starts were charged against the 424-start limit.

| Processing assumption | Model | Passed stopping checks | Unresolved | Error |
|---|---|---:|---:|---:|
| No Earth-rate removal | Rotating globe | 25 | 28 | 0 |
| No Earth-rate removal | Still globe | 39 | 14 | 0 |
| No Earth-rate removal | Flat disc | 37 | 16 | 0 |
| Possible Earth-rate removal | Rotating globe | 18 | 35 | 0 |
| Possible Earth-rate removal | Still globe | 34 | 19 | 0 |
| Possible Earth-rate removal | Flat disc | 35 | 18 | 0 |

Convergence requires the numerical stopping and stationarity checks. A low residual alone is insufficient; an unresolved optimization cannot rule out its model.

## Fully converged versus unresolved stretches

A fully converged stretch has all six required fits. Any unresolved or failed fit leaves its stretch in the unresolved group. Geometry was selected before any model comparison.

| Group | Stretches | Total minutes | Median duration (min) | Median ground speed (km/h) | IMU types (stretch counts) |
|---|---:|---:|---:|---:|---|
| fully converged | 12 | 87.6 | 7.3 | 822.9 | 21: 12 |
| unresolved | 41 | 336.6 | 8.9 | 834.7 | 8: 2, 21: 39 |
| unsupported | 0 | 0 | — | — | — |

These are descriptive comparisons, not evidence that speed, duration or instrument type caused convergence. All selected stretches remain in the report.

## Source recordings and tracks

Every stretch uses Applanix Group-4 IMU increments at nominal 200 Hz. IMU type is the logged type code, not a confirmed manufacturer/model. Exact original filenames, SHA-256 fingerprints, UTC bounds, mounting epochs and conversion details are in [the stretch ledger](stretch-summary.csv). [Receiver track points](tracks.csv) retain the dated positions without interpolation.

| Stretch | UTC start | IMU type | Minutes | Ground speed min/median (km/h) | GPS track (km) | Shape |
|---|---|---:|---:|---:|---:|---|
| b365bdf39150ee6afc303ac1 | 2009-10-20T13:25:32.783556Z | 8 | 9.8 | 841.4/849.1 | 137.3 | unresolved |
| 034547522e2d98947b598466 | 2009-10-20T13:23:57.047162Z | 21 | 10.8 | 837.6/848.7 | 151.8 | unresolved |
| 3df34ea39a6cbdbe15bb0f36 | 2009-10-24T13:25:51.649791Z | 8 | 11.1 | 851.9/858.0 | 158.3 | unresolved |
| 233183f67270980491416678 | 2009-10-24T13:25:59.003646Z | 21 | 11.1 | 852.0/858.1 | 157.8 | unresolved |
| c16df82d514fc69d11d941d2 | 2009-10-25T14:57:57.272991Z | 21 | 10.8 | 839.8/843.1 | 151.1 | unresolved |
| fad74da3a09951b31e882472 | 2009-10-27T13:28:57.062636Z | 21 | 5.5 | 787.1/790.3 | 72.4 | unresolved |
| 0e73879f98c3b701fd7c42df | 2009-10-29T13:26:58.932564Z | 21 | 11.1 | 836.1/837.7 | 154.8 | unresolved |
| fd7b81e48a4122b149c4925b | 2009-11-05T14:40:28.063157Z | 21 | 5.9 | 718.2/737.1 | 71.8 | unresolved |
| 7024120d59221e8eaf127084 | 2010-03-22T07:52:03.263559Z | 21 | 7.3 | 801.8/820.7 | 98.9 | globe |
| b4ab6e128de963c2ce69aa51 | 2010-03-29T13:06:37.134207Z | 21 | 6.9 | 862.3/863.2 | 98.2 | unresolved |
| 7df21c836bec5751f83c0cce | 2010-04-09T12:56:16.115058Z | 21 | 4.1 | 834.3/841.7 | 56.5 | unresolved |
| bb8061a43b4f14b6262ceda1 | 2010-04-14T12:41:33.104523Z | 21 | 6.4 | 793.7/794.4 | 84.1 | unresolved |
| 48c1bfe2f1aeb31c9386841d | 2011-10-08T15:00:19Z | 21 | 7.1 | 891.4/904.5 | 106.5 | unresolved |
| 8bf60391909fe8988c23621a | 2011-10-10T12:20:04.228661Z | 21 | 6.3 | 788.1/796.4 | 82.8 | unresolved |
| 2791235ca0b11b1ef4386e21 | 2011-10-12T12:05:40Z | 21 | 7.4 | 809.3/822.5 | 100.7 | unresolved |
| 2f7e37c48f3b4423c55662dd | 2015-09-24T13:19:15.032273Z | 21 | 9.4 | 741.4/755.6 | 117.6 | globe |
| d9d91c8edba5721931856fc9 | 2015-09-24T12:47:53Z | 21 | 7.3 | 788.8/793.6 | 96.7 | unresolved |
| da346f70a6661ee42cecea19 | 2015-09-24T13:06:34Z | 21 | 9.1 | 769.8/784.8 | 118.2 | unresolved |
| e6629f14d2e03e471a446e06 | 2015-09-26T14:02:21.171782Z | 21 | 9.2 | 791.9/798.3 | 121.6 | unresolved |
| f7677e15295077fd8cfd3089 | 2015-09-26T13:25:00Z | 21 | 7.3 | 820.0/825.2 | 100.4 | globe |
| abe881b5c87cc878226a9aef | 2015-09-26T14:01:50Z | 21 | 8.9 | 791.9/797.8 | 118.5 | globe |
| 01177d345ecb28bcfdcc6a4f | 2015-09-29T12:48:57.087609Z | 21 | 8.5 | 884.6/888.0 | 125.4 | unresolved |
| dac266ab5c198050d25b17f6 | 2015-09-29T12:47:39Z | 21 | 8.9 | 884.6/887.9 | 131.0 | unresolved |
| f50ff54d2e6175d2e8277823 | 2015-10-03T14:18:43.047077Z | 21 | 9.1 | 881.4/894.0 | 135.0 | unresolved |
| 4fad619380ea429cbf6cbcc9 | 2015-10-03T14:01:56.618753Z | 21 | 4.7 | 905.5/915.8 | 71.4 | unresolved |
| d4e793dd58b79bf4d95c692b | 2015-10-03T14:18:15Z | 21 | 8.9 | 881.4/895.6 | 131.6 | unresolved |
| 570b37d23af5e245dd461051 | 2015-10-05T12:45:50Z | 21 | 7.3 | 859.5/878.1 | 106.6 | globe |
| 8dacbcf9f1e2774318723460 | 2015-10-05T13:08:08Z | 21 | 6.4 | 828.8/847.8 | 90.3 | globe |
| a953c8ddf4fae255674de128 | 2015-10-07T13:27:51.097754Z | 21 | 9.1 | 837.6/854.6 | 128.4 | unresolved |
| 711e7aade97a54f71ac5d9c5 | 2015-10-07T12:54:45.006409Z | 21 | 5.6 | 755.1/772.6 | 70.8 | globe |
| 31d7e5019dfdc9e2e6387206 | 2015-10-07T13:27:38Z | 21 | 8.9 | 837.7/854.2 | 125.7 | globe |
| f66ab49757292bc3c396aba2 | 2015-10-10T14:14:55Z | 21 | 9.3 | 900.7/913.9 | 141.4 | unresolved |
| e543e7b6e878b96a1966dbb6 | 2015-10-10T13:51:59Z | 21 | 7.1 | 816.6/823.4 | 96.8 | unresolved |
| 9f4d888995ab94bb8eff4df6 | 2015-10-10T14:12:28Z | 21 | 9.2 | 900.7/914.2 | 139.4 | unresolved |
| 705de394963c8be15c580512 | 2015-10-12T13:26:58.778403Z | 21 | 4.0 | 786.5/795.9 | 52.7 | unresolved |
| 74ec8f62cb621604ddcdde9c | 2015-10-12T13:15:12Z | 21 | 8.6 | 820.4/828.4 | 118.0 | unresolved |
| a6e658d1550299e4eb9f00a3 | 2015-10-17T13:17:44Z | 21 | 9.0 | 775.5/779.1 | 117.0 | unresolved |
| 8f2a00e9f13b367202e4d46a | 2015-10-17T12:54:03Z | 21 | 7.3 | 748.9/755.5 | 91.2 | globe |
| 8cc288f5de7e88878c04b7f1 | 2015-10-17T13:17:05Z | 21 | 8.8 | 775.6/779.1 | 114.5 | unresolved |
| 50f24131843071ae9312c082 | 2015-10-20T13:17:24Z | 21 | 9.2 | 749.7/753.8 | 115.5 | unresolved |
| be1d75a0e47ff1c972865ba7 | 2015-10-20T12:54:29Z | 21 | 7.2 | 752.0/761.1 | 91.8 | unresolved |
| 61e1b08da0912019eb521cd9 | 2015-10-20T13:15:17Z | 21 | 8.9 | 746.7/754.1 | 111.5 | unresolved |
| ec6effbf9b2172b1389afc96 | 2015-10-22T13:14:24Z | 21 | 6.2 | 807.7/825.0 | 84.7 | globe |
| c69d0a93113d86b5264f92eb | 2015-10-22T12:53:27Z | 21 | 7.2 | 712.0/726.5 | 86.7 | globe |
| 370cec66878c4c1cf84b4ceb | 2015-10-25T13:14:25Z | 21 | 9.2 | 811.8/816.9 | 124.9 | unresolved |
| b4e44ddc0f130ecd45674c78 | 2015-10-25T12:52:41Z | 21 | 7.2 | 822.0/824.9 | 98.8 | unresolved |
| 2eb8727803b318a39937e7ec | 2015-10-25T13:09:19Z | 21 | 9.0 | 811.8/823.6 | 122.2 | unresolved |
| 2a56eb8fa7d4e10c9a867bb0 | 2015-10-27T14:27:23Z | 21 | 9.1 | 829.8/834.7 | 126.6 | unresolved |
| f5c1fca513b9b40dffba93eb | 2015-10-27T14:02:23Z | 21 | 4.5 | 833.8/842.8 | 62.9 | unresolved |
| 013fdb894ff28509889a8896 | 2015-10-27T14:25:35Z | 21 | 8.9 | 829.9/834.5 | 123.5 | unresolved |
| 5a642167dfb523f6c9cc284c | 2015-10-29T13:16:56Z | 21 | 9.2 | 868.4/879.9 | 134.4 | unresolved |
| c028fde63f91c3f1067df4ad | 2015-10-29T12:57:46Z | 21 | 5.9 | 828.3/835.0 | 81.6 | globe |
| 7ee5e21c025360c970124eeb | 2015-10-29T13:11:09.888451Z | 21 | 8.9 | 883.6/892.4 | 131.7 | unresolved |

Track distance sums receiver-position steps using a 6,371 km spherical coordinate convention. It is a route description, not evidence for a globe. Ground speed is receiver speed; it is not true airspeed.

## Partial comparisons in indeterminate stretches

These rows show only matched globe/disc pairs whose two fits converged. An unfinished fit is never treated as a losing model. A pairwise lean does not resolve the whole stretch or unlock a rotation decision. Numerical costs have no calibrated significance here.

| Stretch | Processing assumption | Converged models | Available shape lean |
|---|---|---|---|
| b365bdf39150ee6afc303ac1 | No Earth-rate removal | None | No converged shape pair |
| b365bdf39150ee6afc303ac1 | Possible Earth-rate removal | None | No converged shape pair |
| 034547522e2d98947b598466 | No Earth-rate removal | Flat disc | No converged shape pair |
| 034547522e2d98947b598466 | Possible Earth-rate removal | None | No converged shape pair |
| 3df34ea39a6cbdbe15bb0f36 | No Earth-rate removal | Still globe, Flat disc | Flat fits better than still globe |
| 3df34ea39a6cbdbe15bb0f36 | Possible Earth-rate removal | Still globe, Flat disc | Flat fits better than still globe |
| 233183f67270980491416678 | No Earth-rate removal | Still globe | No converged shape pair |
| 233183f67270980491416678 | Possible Earth-rate removal | Still globe | No converged shape pair |
| c16df82d514fc69d11d941d2 | No Earth-rate removal | Still globe, Flat disc | Still globe fits better than flat |
| c16df82d514fc69d11d941d2 | Possible Earth-rate removal | Still globe, Flat disc | Still globe fits better than flat |
| fad74da3a09951b31e882472 | No Earth-rate removal | None | No converged shape pair |
| fad74da3a09951b31e882472 | Possible Earth-rate removal | None | No converged shape pair |
| 0e73879f98c3b701fd7c42df | No Earth-rate removal | Flat disc | No converged shape pair |
| 0e73879f98c3b701fd7c42df | Possible Earth-rate removal | Flat disc | No converged shape pair |
| fd7b81e48a4122b149c4925b | No Earth-rate removal | Still globe, Flat disc | Still globe fits better than flat |
| fd7b81e48a4122b149c4925b | Possible Earth-rate removal | Still globe, Flat disc | Still globe fits better than flat |
| b4ab6e128de963c2ce69aa51 | No Earth-rate removal | Rotating globe, Flat disc | Rotating globe fits better than flat |
| b4ab6e128de963c2ce69aa51 | Possible Earth-rate removal | Rotating globe, Flat disc | Rotating globe fits better than flat |
| 7df21c836bec5751f83c0cce | No Earth-rate removal | None | No converged shape pair |
| 7df21c836bec5751f83c0cce | Possible Earth-rate removal | None | No converged shape pair |
| bb8061a43b4f14b6262ceda1 | No Earth-rate removal | None | No converged shape pair |
| bb8061a43b4f14b6262ceda1 | Possible Earth-rate removal | None | No converged shape pair |
| 48c1bfe2f1aeb31c9386841d | No Earth-rate removal | Rotating globe, Still globe | No converged shape pair |
| 48c1bfe2f1aeb31c9386841d | Possible Earth-rate removal | None | No converged shape pair |
| 8bf60391909fe8988c23621a | No Earth-rate removal | Still globe, Flat disc | Still globe fits better than flat |
| 8bf60391909fe8988c23621a | Possible Earth-rate removal | Still globe | No converged shape pair |
| 2791235ca0b11b1ef4386e21 | No Earth-rate removal | Still globe, Flat disc | Flat fits better than still globe |
| 2791235ca0b11b1ef4386e21 | Possible Earth-rate removal | Still globe, Flat disc | Flat fits better than still globe |
| d9d91c8edba5721931856fc9 | No Earth-rate removal | Still globe, Flat disc | Still globe fits better than flat |
| d9d91c8edba5721931856fc9 | Possible Earth-rate removal | Still globe, Flat disc | Still globe fits better than flat |
| da346f70a6661ee42cecea19 | No Earth-rate removal | Still globe, Flat disc | Still globe fits better than flat |
| da346f70a6661ee42cecea19 | Possible Earth-rate removal | Still globe | No converged shape pair |
| e6629f14d2e03e471a446e06 | No Earth-rate removal | Rotating globe, Still globe | No converged shape pair |
| e6629f14d2e03e471a446e06 | Possible Earth-rate removal | Rotating globe | No converged shape pair |
| 01177d345ecb28bcfdcc6a4f | No Earth-rate removal | Still globe | No converged shape pair |
| 01177d345ecb28bcfdcc6a4f | Possible Earth-rate removal | Still globe | No converged shape pair |
| dac266ab5c198050d25b17f6 | No Earth-rate removal | Flat disc | No converged shape pair |
| dac266ab5c198050d25b17f6 | Possible Earth-rate removal | Flat disc | No converged shape pair |
| f50ff54d2e6175d2e8277823 | No Earth-rate removal | Still globe | No converged shape pair |
| f50ff54d2e6175d2e8277823 | Possible Earth-rate removal | Still globe, Flat disc | Flat fits better than still globe |
| 4fad619380ea429cbf6cbcc9 | No Earth-rate removal | Rotating globe, Still globe, Flat disc | Rotating globe fits better than flat; Flat fits better than still globe |
| 4fad619380ea429cbf6cbcc9 | Possible Earth-rate removal | Still globe, Flat disc | Flat fits better than still globe |
| d4e793dd58b79bf4d95c692b | No Earth-rate removal | Rotating globe, Still globe | No converged shape pair |
| d4e793dd58b79bf4d95c692b | Possible Earth-rate removal | Still globe | No converged shape pair |
| a953c8ddf4fae255674de128 | No Earth-rate removal | Rotating globe, Still globe, Flat disc | Rotating globe fits better than flat; Flat fits better than still globe |
| a953c8ddf4fae255674de128 | Possible Earth-rate removal | Still globe, Flat disc | Flat fits better than still globe |
| f66ab49757292bc3c396aba2 | No Earth-rate removal | Rotating globe, Still globe, Flat disc | Rotating globe fits better than flat; Flat fits better than still globe |
| f66ab49757292bc3c396aba2 | Possible Earth-rate removal | Flat disc | No converged shape pair |
| e543e7b6e878b96a1966dbb6 | No Earth-rate removal | Flat disc | No converged shape pair |
| e543e7b6e878b96a1966dbb6 | Possible Earth-rate removal | Rotating globe, Flat disc | Rotating globe fits better than flat |
| 9f4d888995ab94bb8eff4df6 | No Earth-rate removal | Still globe | No converged shape pair |
| 9f4d888995ab94bb8eff4df6 | Possible Earth-rate removal | Still globe | No converged shape pair |
| 705de394963c8be15c580512 | No Earth-rate removal | Still globe, Flat disc | Still globe fits better than flat |
| 705de394963c8be15c580512 | Possible Earth-rate removal | Rotating globe, Still globe, Flat disc | Rotating globe fits better than flat; Still globe fits better than flat |
| 74ec8f62cb621604ddcdde9c | No Earth-rate removal | Rotating globe, Still globe, Flat disc | Rotating globe fits better than flat; Still globe fits better than flat |
| 74ec8f62cb621604ddcdde9c | Possible Earth-rate removal | Still globe, Flat disc | Still globe fits better than flat |
| a6e658d1550299e4eb9f00a3 | No Earth-rate removal | Flat disc | No converged shape pair |
| a6e658d1550299e4eb9f00a3 | Possible Earth-rate removal | Still globe, Flat disc | Still globe fits better than flat |
| 8cc288f5de7e88878c04b7f1 | No Earth-rate removal | Still globe, Flat disc | Still globe fits better than flat |
| 8cc288f5de7e88878c04b7f1 | Possible Earth-rate removal | Flat disc | No converged shape pair |
| 50f24131843071ae9312c082 | No Earth-rate removal | Flat disc | No converged shape pair |
| 50f24131843071ae9312c082 | Possible Earth-rate removal | Flat disc | No converged shape pair |
| be1d75a0e47ff1c972865ba7 | No Earth-rate removal | Rotating globe, Still globe | No converged shape pair |
| be1d75a0e47ff1c972865ba7 | Possible Earth-rate removal | Rotating globe, Still globe | No converged shape pair |
| 61e1b08da0912019eb521cd9 | No Earth-rate removal | Rotating globe, Flat disc | Rotating globe fits better than flat |
| 61e1b08da0912019eb521cd9 | Possible Earth-rate removal | None | No converged shape pair |
| 370cec66878c4c1cf84b4ceb | No Earth-rate removal | Rotating globe | No converged shape pair |
| 370cec66878c4c1cf84b4ceb | Possible Earth-rate removal | Flat disc | No converged shape pair |
| b4e44ddc0f130ecd45674c78 | No Earth-rate removal | Rotating globe, Still globe, Flat disc | Rotating globe fits better than flat; Still globe fits better than flat |
| b4e44ddc0f130ecd45674c78 | Possible Earth-rate removal | Still globe, Flat disc | Still globe fits better than flat |
| 2eb8727803b318a39937e7ec | No Earth-rate removal | Still globe | No converged shape pair |
| 2eb8727803b318a39937e7ec | Possible Earth-rate removal | None | No converged shape pair |
| 2a56eb8fa7d4e10c9a867bb0 | No Earth-rate removal | Rotating globe, Still globe | No converged shape pair |
| 2a56eb8fa7d4e10c9a867bb0 | Possible Earth-rate removal | None | No converged shape pair |
| f5c1fca513b9b40dffba93eb | No Earth-rate removal | Still globe, Flat disc | Flat fits better than still globe |
| f5c1fca513b9b40dffba93eb | Possible Earth-rate removal | Still globe, Flat disc | Flat fits better than still globe |
| 013fdb894ff28509889a8896 | No Earth-rate removal | None | No converged shape pair |
| 013fdb894ff28509889a8896 | Possible Earth-rate removal | None | No converged shape pair |
| 5a642167dfb523f6c9cc284c | No Earth-rate removal | Still globe, Flat disc | Flat fits better than still globe |
| 5a642167dfb523f6c9cc284c | Possible Earth-rate removal | Rotating globe, Still globe, Flat disc | Rotating globe fits better than flat; Flat fits better than still globe |
| 7ee5e21c025360c970124eeb | No Earth-rate removal | Still globe, Flat disc | Flat fits better than still globe |
| 7ee5e21c025360c970124eeb | Possible Earth-rate removal | Still globe, Flat disc | Flat fits better than still globe |

[Case-by-case details](case-summary.csv) preserve the available cost differences and unresolved models; [fit details](fit-summary.csv) also preserve unfinished costs as diagnostics. They are not used to rank models whose fits have not converged.

## Residuals and limits

| Fit group | Fits touching a parameter limit | Fits using 200 evaluations | Median RMS N/E/up (m) |
|---|---:|---:|---|
| converged | 188 | 2 | 9.70/15.41/1.19 |
| unresolved | 129 | 103 | 1.08/1.52/0.92 |
| failed | 0 | 0 | — |

Residuals from unresolved fits describe unfinished solutions; they do not support model rejection. A converged fit at a parameter limit can still be sensitive to the assumed bounds. Smaller sections are fixed-parameter consistency checks, not extra trials.

Calibration offsets, onboard corrections, the integration clock and receiver uncertainty remain partly assumed. Numerical convergence does not establish model adequacy, a global optimum or a validated error rate. All scientific decisions still abstain.

[Every stretch](stretch-summary.csv) and [every fit](fit-summary.csv) retain unresolved outcomes, solver messages and diagnostics. See [selection criteria](ELIGIBILITY.md), [methods](README.md) and [pilot findings](../ilvis0-refinement-20261008/PROVISIONAL.md).
