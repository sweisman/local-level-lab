# Clock-aware bounds improve, but remain too broad

All **48 generated sector identities pass correctness**. Each complete
model/processing comparison retains its known future truth and all eight
original yaw sectors. Inputs and physical calibration bounds are unchanged.

Typical globe range widths are now about **115 m north, 115 m east and 115 m
in height**, compared with 386 / 172 / 118 m in the earlier orientation cover.
The clock-aware construction removes about 70% of the remaining north width
and one third of the east width. Height changes little.

Relative to the original broad-box method, the improvement is approximately
**6.7-fold north, 5.1-fold east and 4.5-fold vertically**. None of the six cases
meets the predeclared tenfold target on every axis. These calculated ranges
remain far too broad to qualify long-record prediction uncertainty. They are
not measured aircraft errors, sensor drift or a revision of the 53 model
preferences.

The study spent 192 native evaluations in 472 seconds, within its separate
finite allowance. It saves every native value, all 27 Jacobian columns,
training observation/inequality and future support input. Its earlier
qualification includes all candidates, processing cases, timing boundaries
and independent stationary poses. Neither study may be restarted or expanded.

## Remaining width

For the first specified-field/no-removal case, the largest retained nonlinear
allowance contributes roughly **52 m on each axis**; affine uncertainty adds
about **63 m**. Training remainder allowances already measure about 19 m at
the first 0.2-second epoch and 24 m at 1.5 seconds. This points to a remaining
loss in the calibration/error enclosure, rather than a need to adjust the
physical model or widen an instrument drift assumption.

The next saved-data audit will quantify which calibration ranges can actually
be narrowed by the joint training inequalities, and which broad remainders
remain even with tighter affine calculations. Errors shared across epochs
must be distinguished from independently varying errors. The audit needs no
new native predictions or original IMU reads.

Global numerical treatment, actual receiver-error adequacy and independent
confirmation remain open. New qualified aircraft prediction fits remain
blocked. The main numerical result stays **53 globe preferences, zero flat
preferences and zero unresolved**.

[All six unions and both comparisons](README.md) · [Frozen allowance](PLAN.md) ·
[Saved-calibration audit plan](../ilvis0-regrouped-constraint-audit/PLAN.md) ·
[Native qualification](../ilvis0-regrouped-controls/INTERPRETATION.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
