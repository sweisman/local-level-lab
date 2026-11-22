# The saved GPS correction leaves the gyro-free motion ranges overlapping

The four Earth-model cases still overlap in every matched comparison on
the IMU8 recording. The largest change to any rate bound was under
0.00008°/s. The check used the exact GPS correction that cleared the
earlier force-magnitude gaps. Its largest position change was 27.2 cm.
[Force-magnitude check](SHARED_FORCE_WITNESS_RESULT.md)

| Part of recording | Sampled directions | Integration clock | Common rate range |
| --- | ---: | --- | ---: |
| Earlier | 415 | Nominal 200 Hz | 3.9402–4.0673°/s |
| Earlier | 415 | Packet-header time | 3.9399–4.0670°/s |
| Later | 193 | Nominal 200 Hz | 3.8543–3.9531°/s |
| Later | 193 | Packet-header time | 3.8539–3.9528°/s |

Each model's lower bound comes from how quickly an orientation would have
to change to align the measured and required force directions. Its upper
bound comes from a verified example of such a path. The model-specific
ranges overlap. Four midpoint probes verified a nominal path and twelve
were inconclusive. No probe raised a lower bound by exclusion.

The test reused all original GPS timestamps and selected accelerometer
packets. It evaluated 608 paths, 4,864 force points and 16 midpoint
probes. It used no gyroscope measurements or new navigation fits. The
original GPS and carrier-phase comparisons are preserved for both IMU
types. [Original rate comparisons](RECORDED_MOTION_RATE_RESULT.md)

The overlap means this sampled rate check cannot separate the four
cases. A joint comparison still needs independently supported limits on
aircraft motion and a model of receiver error across time.

[Frozen plan](SHARED_GPS_MOTION_RATE_PLAN.md) ·
[All original and corrected bounds](shared-gps-motion-rate.json) ·
[Verified replay bundle](shared-gps-motion-rate-evidence/replay.zip)
