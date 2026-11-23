# Sampled force directions call for more rotation than either gyro records

On the 24 October 2009 flight, the acceleration-only paths frequently
required more angular travel than either gyro recorded over the same
interval. This held for all four Earth and background-field candidates,
both receiver paths and both packet clocks.

| Portion of the recording | Matched intervals per setting | Intervals exceeding both recorded budgets | Largest shortfall in each setting |
| --- | ---: | ---: | ---: |
| Earlier | 414 | 303–309 | 3.09–3.12°/s |
| Later | 192 | 149–150 | 2.90–2.95°/s |

The recorded budget adds the magnitude of every gyro increment touching
the interval. It includes an extra 0.15 seconds on each side, a half-count
allowance on every gyro axis, and the specified frame-rate allowance.
The comparison uses whichever recorder gives the larger budget at each
interval. The shortfall is the remaining angle divided by the original
interval duration. These readings cannot bound motion inside a packet.

The result identifies a mismatch in the joint assumptions. Treating one
acceleration packet's mean direction as its midpoint direction, using
the fixed receiver paths, and taking the logged gyro travel as the motion
budget fail together in numerous intervals. Unresolved filtering, local
vibration, mounting and calibration are possible contributors. The mismatch
appears across all four candidates and supplies no shape decision.

The first attempt stopped on a source mismatch with the 20 October pair.
The [corrected source binding](PAIRED_GYRO_INTERVAL_SOURCE_BINDING.md)
verified both 24 October originals before replaying the fixed histories.
All 32 summaries completed, with no navigation fits or Group 1 observations.
[Frozen calculation](PAIRED_GYRO_INTERVAL_PLAN.md) ·
[All summaries and both execution receipts](paired-gyro-intervals-result.json)

A follow-up kept the same interval centers and averaged the force at
each endpoint. Both averaging widths cleared the recorded budget on
every interval. [Averaged force result](PAIRED_GYRO_AVERAGED_FORCE_RESULT.md)
