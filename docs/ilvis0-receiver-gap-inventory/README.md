# Receiver coverage in the 53 selected stretches

The primary GPS receiver supplies positions for **52 of the 53** previously
selected aircraft stretches. In each of those 52, its saved position records
form one uninterrupted block under the declared **1.5-second maximum gap**.
The blocks last **4.0–11.1 minutes** and contain **124,637 positions** in all.
The remaining recording had already failed strict receiver decoding; it stays
in the count as an abstention. No gaps were filled and no stretch was replaced.

The [per-stretch table](stretches.csv) gives the original recording, selected
times, row counts, block count and disposition. The [block table](blocks.csv)
preserves each original receiver-table row range and its GPS times. Both were
generated solely from hash-checked, sealed study results; the
[receipt](receipt.json) records their source and output hashes. The
[frozen plan](PLAN.md) fixes the cohort, gap rule and finite execution limits.

This is a **GPS coverage check**, not a new IMU fit or Earth-model result.
The receiver positions have not thereby acquired a calibrated error model.
The next channel-contribution study still needs that model, plus a qualified
comparison of the recorded accelerometer and gyroscope observations on the
same selected support.
