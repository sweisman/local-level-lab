# Packet timing limits the paired accelerometer check

Comparing the companion recorder on the original NASA force-test windows
leaves too much uncertainty at packet edges to establish the needed accuracy.
The mixed IMU8 and IMU21 pair shows a small discrepancy at the logged time
alignment. Allowing 5 ms of relative clock displacement removes the positive
lower bound. The two IMU21 streams have no positive lower bound even at the
logged alignment.

| Recorder pair | Relative clock allowance | Later windows retained | Median width of the companion force interval | Minimum joint discrepancy |
|---|---:|---:|---:|---:|
| IMU8 and IMU21 | Logged elapsed time | 133 | 3.386 mm/s² | 0.744 mm/s² |
| IMU8 and IMU21 | ±5 ms | 133 | 10.028 mm/s² | 0 within the interval bound |
| Two IMU21 streams | Logged elapsed time | 150 | 3.321 mm/s² | 0 within the interval bound |
| Two IMU21 streams | ±5 ms | 150 | 9.905 mm/s² | 0 within the interval bound |

The table uses the packet-header clock. The nominal clock gives the same
pattern, with a minimum joint discrepancy of 0.900 mm/s² for the mixed pair
at the logged alignment. The widest tested clock range, ±300 ms, also leaves
agreement possible for both pairs under the interval calculation. No packet
was split or interpolated. The force interval spans the amount inside the
window and the amount contributed by all packets that could touch it.

If the mixed pair measures one common history, the 0.744 mm/s² discrepancy
requires an error of at least 0.323 mm/s² on at least one recorder somewhere in
the combined record, under this calibration and clock assumption. The earlier
data alone require 0.504 mm/s² of joint allowance. This diagnostic allows one
constant gain and offset for the whole record. In the settings where the bounds
contain agreement, the actual packets could still disagree. Neither result
measures differences in motion at the mounts, the amount of force within a
packet, or an error shared by both recorders.

The interval width exceeds the [force discrimination targets](FORCE_GAIN_RANGE_RESULT.md)
for the two IMU21 streams even at the logged alignment. For this method to test
those targets, it would need tighter information on how much of a packet's
force belongs inside each window. The gyro-free shape result remains open.

Two tasks passed. They used two companion decodes, 14 charged operations and
zero new Earth-model fits or propagations. The first software check expected an
exact zero as an upper endpoint. The passing check verifies that the interval
encloses zero within the frozen rounding allowance. The original test record
is retained.

[Frozen method](PAIRED_FORCE_WINDOW_PLAN.md) ·
[All support and discrepancy summaries](paired-force-window-result.json) ·
[Verified evidence](paired-force-window-evidence/README.md)
