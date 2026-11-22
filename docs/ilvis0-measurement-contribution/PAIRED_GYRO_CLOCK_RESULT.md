# One-packet shifts explain little of the paired gyro disagreement

Every earlier-data fit chose a shift of one 5 ms sample in either direction.
The shift reduced later short-window disagreement in six of eight comparisons,
by at most 4.6%. At ten seconds, only three comparisons improved. Most of the
recorder disagreement remained.

| Pair | Packet clock | Window | Earlier-selected shift | Later vector RMS before → after |
|---|---|---:|---:|---:|
| IMU8 with IMU21 | Nominal | 0.25 s | −5 ms | 60.41 → 61.07°/h |
| IMU8 with IMU21 | Nominal | 1 s | +5 ms | 17.10 → 16.31°/h |
| IMU8 with IMU21 | Elapsed header | 0.25 s | −5 ms | 59.81 → 59.97°/h |
| IMU8 with IMU21 | Elapsed header | 1 s | +5 ms | 15.20 → 15.10°/h |
| Two IMU21 recorders | Nominal | 0.25 s | −5 ms | 22.36 → 21.57°/h |
| Two IMU21 recorders | Nominal | 1 s | −5 ms | 8.12 → 7.95°/h |
| Two IMU21 recorders | Elapsed header | 0.25 s | −5 ms | 22.36 → 21.57°/h |
| Two IMU21 recorders | Elapsed header | 1 s | −5 ms | 8.12 → 7.95°/h |

Each line uses a common set of windows across every tested shift. Both the
unshifted and shifted comparisons used an earlier-only relative rotation and
rate offset. The mixed pair changed its preferred shift when the window length
changed. The two IMU21 units picked the same shift, with modest later gains
at both window lengths. A selected shift can also reflect packet assignment,
filtering or motion at the recorder mounts. These differences alone leave the
true timing and absolute gyro errors open.

The run verified four original recorder files and used whole angle increments.
Both tasks completed in 21.53 seconds on two one-thread workers, with 988
charged operations and zero Earth-model fits. Ten focused checks passed,
including a known delay and a change that was confined to the later data.

[Frozen method](PAIRED_GYRO_CLOCK_PLAN.md) ·
[Complete shift curves and scores](paired-gyro-clock-result.json) ·
[Verified run evidence](paired-gyro-clock-evidence/README.md)
