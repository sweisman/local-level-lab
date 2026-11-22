# Native forecast error at two cuts on the same ESA flight

Both cuts on development recording 187 forecast 120 receiver reports
that were withheld from their respective fits. Four technical replays
reproduced the archived covariance identities, means and marginal
covariances exactly. The earlier joint scores were saved before
the later receiver window was read for this check.

| IMU error description | Earlier mean squared standardized error | Later mean squared standardized error | Later / earlier |
|---|---:|---:|---:|
| Recorded increments | 0.01120 | 0.04548 | 4.0592× |
| Sampled rate points | 0.01120 | 0.04548 | 4.0592× |

The later RMS standardized error is about twice the earlier RMS under
either description. Both windows remain below the unit working scale.
Using an earlier held-out score avoids comparing the later forecast
with residuals on the data that determined the fit. The comparable
[simplified error laws](ESA_ROLLING_SCALE_TRANSFER_RESULT.md)
gave later-to-earlier squared ratios from 3.31 to 3.70.

The growth is uneven across the three channels of the joint score.
For the increment description, the later squared score per component
is 6.76 times the earlier value in the north-ordered channel, 44.8
times in the east-ordered channel and 0.88 times in the height-ordered
channel. The channels come from sequentially removing the correlation
in the reported positions. They cannot identify a particular inertial
sensor or receiver error as the cause. Compare direction-dependent
changes before freezing an aircraft forecast rule based on one scale.

These are two disjoint scoring windows from one flight. The later fit
had access to the earlier scoring observations. The comparison is
development evidence about error transfer. A rule for new aircraft
still needs supporting error measurements and independent validation.
No fits were repeated and no reserved flights were opened.

[Fixed study plan](ESA_NATIVE_ROLLING_TRANSFER_PLAN.md) ·
[Earlier scoring receipt](esa-native-rolling-transfer-earlier.json) ·
[Full comparison](esa-native-rolling-transfer-result.json)

The closed study is `esa-native-rolling-transfer-v1-20261118`, with
manifest SHA-256 `1bec76a051028709ff4a9bc658c88b1b37b84d36dab799ce709c32b4e3d9a6c6`.
Each of the four tasks retains a `rolling-factors.npz` snapshot and
its `factor-replay.json` receipt.
