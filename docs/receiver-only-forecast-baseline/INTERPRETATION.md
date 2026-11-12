# What the receiver-only forecast adds

The three NASA pilot recordings now have a matched, simple GPS-only forecast:
fit constant velocity from the last minute of **earlier** receiver positions,
then predict the same withheld positions used by the IMU study. The forecast
never uses IMU samples. All three calculations completed and their saved
signed errors reproduce the published scores.

| Recording | Receiver-only horizontal RMS | Best available field-globe IMU comparison |
|---|---:|---:|
| A, southern IMU8 | 351.45 m | 15.5–19.3 m among qualified starts; no complete three-model setting |
| B, northern IMU21 | 199.21 m | 0.84–1.13 m; all four matched settings complete |
| C, southern IMU21 | 86.55 m | 3.30 m in the one complete matched setting |

The direct comparison is strongest on **B**: the same withheld receiver
positions are predicted much more closely when the earlier fitted physical
model is propagated with IMU measurements. A and C also show smaller available
IMU forecast errors, but their missing model fits limit the complete
three-candidate comparison. The receiver-only rule is deliberately simple; a
more flexible GPS-only motion model could do better. This check therefore
shows incremental prediction over a fixed constant-velocity baseline. It does
**not** prove that gyroscopes alone caused the gain, or establish curvature,
confidence, physical adequacy, or an independent flight replication.
The [separate spherical-path control](../receiver-only-geodesic-control/INTERPRETATION.md)
tests one stronger GPS-only rule on the same withheld positions. It reduces
horizontal errors to 151.91 m on A, 189.26 m on B and 33.14 m on C; the full
IMU comparison on B remains much closer.

The receiver-only height RMS values are 7.09 m on A, 19.24 m on B and 9.13 m
on C. Horizontal and height outcomes must be kept separate: a low horizontal
error cannot rescue an implausible altitude reconstruction. The baseline
uses conventional receiver coordinates as its prediction target and makes no
globe/disc decision.

[Saved baseline results](README.md) · [All scores](results.csv) ·
[Matched IMU pilot](../ilvis0-retrospective-prediction-pilot-v2/INTERPRETATION.md) ·
[Frozen method](PLAN.md)
