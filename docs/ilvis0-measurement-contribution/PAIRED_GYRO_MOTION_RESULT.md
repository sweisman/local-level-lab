# Two recorders give different short-timescale motion readings

On the same 552-second stretch on 20 October 2009, the IMU8 recorded a peak packet-average
rate of **0.66°/s** and the IMU21 recorded **2.91°/s**. The two packet
clocks gave nearly identical summaries within each recorder. Over one
second, adding the angular travel of each complete packet gave peaks
of **0.32°/s** and **0.77°/s**, respectively.

| Recorder | Packet clock | Peak packet average | Peak with half-count allowance | 95th percentile over 1 s | Peak over 1 s |
| --- | --- | ---: | ---: | ---: | ---: |
| IMU8 | Nominal | 0.657 | 0.695 | 0.176 | 0.316 |
| IMU8 | Header | 0.657 | 0.695 | 0.176 | 0.317 |
| IMU21 | Nominal | 2.906 | 2.906 | 0.720 | 0.765 |
| IMU21 | Header | 2.907 | 2.907 | 0.720 | 0.765 |

All values are in degrees per second. Each row has 552 one-second
intervals with at least 99% support. The one-second statistic adds the
magnitude of each packet, so it includes motion or noise that cancels in
a signed sum. These readings leave the contribution of local vibration,
recorder filtering and gain unresolved.

The [acceleration-only check](RECORDED_MOTION_RATE_RESULT.md) used a
different flight, on 24 October 2009. The source hashes and shared-leg
identifiers establish the distinction. The packet values above describe
the 20 October recording pair. Within-packet motion, instrument filtering
and the physical adequacy of the Earth models remain open.
[Independent source audit](MOTION_SOURCE_AUDIT.md)

The task used two hash-verified originals, and five focused tests passed.
There were zero navigation fits and no Group 1 observations in the check.
[Frozen method](PAIRED_GYRO_MOTION_PLAN.md) ·
[Recorder provenance, all summaries and charges](paired-gyro-motion-result.json)
