# The recorded packets rule out some small force-change limits

The adjacent accelerometer packet averages on both added flights require
rapid changes in the recorded force signal or larger measurement-error
allowances. With an extra allowance of 0.1 m/s² per axis per packet, the
largest lower bounds on force change were **260 m/s³** on IMU8 and
**273 m/s³** on IMU21. Both clocks gave nearly the same results.

| Extra error allowed per axis per packet | IMU8 95th percentile / maximum | IMU21 95th percentile / maximum |
|---|---:|---:|
| 0 m/s² | 149 / 312 m/s³ | 117 / 321 m/s³ |
| 0.02 m/s² | 139 / 301 m/s³ | 107 / 311 m/s³ |
| 0.1 m/s² | 100 / 260 m/s³ | 68 / 273 m/s³ |
| 0.5 m/s² | 0 / 89 m/s³ | 0 / 120 m/s³ |

The table uses the nominal clock. Every row also allows half a count and
up to 15% gain correction per axis. The bounds concern the rate of change
of body-frame force per unit mass. An upper limit below the largest lower
bound is inconsistent with the packets under that row's assumptions.
The calculation leaves the actual upper limit open. It cannot distinguish
aircraft motion, vibration and remaining sensor error. The extra allowances
are sensitivity choices.

The two tasks checked 224,556 adjacent pairs under eight assumptions per
flight. Seven focused tests passed. The saved results keep the earlier
and later periods separate, and the study ran no model fits.

[Frozen method](PACKET_FORCE_CHANGE_PLAN.md) ·
[All clock, error and split results](packet-force-change-result.json) ·
[Reproduction bundle](packet-force-change-evidence/bundle.zip)
