# A mounting-separation correction explains little of the recorder differences

All eight comparisons had enough motion to estimate the three displacement
components. On the mixed IMU8 and IMU21 pair, the correction reduced the
later one-second vector error by about 15%. At ten seconds the reduction was
about 4%. On the two IMU21 recordings the change was less than 1% at either
window length.

| Recorder pair | Window | Later RMS with constant offset | Later RMS with mounting correction | Displacement fitted earlier |
| --- | ---: | ---: | ---: | ---: |
| IMU8 and IMU21 | 1 s | 0.01291 m/s² | 0.01092 m/s² | 23.59 m |
| IMU8 and IMU21 | 10 s | 0.00185 m/s² | 0.00179 m/s² | 16.25 m |
| Two IMU21 | 1 s | 0.002624 m/s² | 0.002606 m/s² | 1.52 m |
| Two IMU21 | 10 s | 0.001391 m/s² | 0.001393 m/s² | 4.73 m |

The table uses the packet-header clock. The nominal clock gives the same
pattern. These are vector differences after earlier-only alignment, so
their RMS values differ from the earlier magnitude-only comparison.
Displacement estimates vary with averaging width even though the physical
mounts are fixed. The results do not establish the distance between the
mounts or an absolute sensor error. The paired comparisons leave the
shape decision open.

Both tasks completed in 21.9 seconds, with 12 charged operations and nine
passing software checks. The two original pairs and packet clocks are
preserved. The study fits relative alignment, offsets and displacement.
It makes no Earth-model fit or receiver-position comparison. Reserved
flights remain unopened.

- [Frozen method](PAIRED_LEVER_ARM_PLAN.md)
- [All eight comparisons and component scores](paired-lever-arm-result.json)
- [Verified run evidence](paired-lever-arm-evidence/README.md)
