# Smaller orientation regions help, but not enough

All **48 generated sector controls pass**. All six complete model/processing
cases retain their known future truth. None of the original yaw range is
discarded: every case keeps all eight sectors, along with all other calibration
directions.

Compared with the saved broad-box construction, future range widths fall to
about **50% north, 29% east and 23% vertically**. That is roughly a twofold to
fourfold improvement. None reaches the predeclared tenfold target. Typical globe
ranges still span about **386 m north, 172 m east and 118 m in height** after
only 1.8 seconds of generated propagation. These are conservative calculated
ranges, not measured aircraft errors or survey-IMU drift.

Both pieces remain important. In the first specified-field/no-removal case,
the largest sector's nonlinear allowance alone contributes about 187 m north,
80 m east and 54 m vertically to its range width. Remaining affine uncertainty
adds about 198 / 91 / 64 m. More precise linear optimization alone cannot remove
the nonlinear contribution.

The completed study spent 192 native evaluations in 411 seconds. It performs
no Earth-model fits, original IMU reads or protected ESA evaluations. Preserve
its source freeze, all sectors and its failure to meet the improvement target;
do not restart it or spend another study's unused allowance.

## A concrete source of overestimation

The current bounds treat each packet's uncertain cutoff separately, even
though every packet shares **one time offset**. Taking absolute remainders
before combining them loses cancellations.

For this generated 400-packet clock and the 1.80 ± 0.15 second query, an exact
rational calculation gives a sum of individual packet-time remainders of
**0.445 seconds**. Multiplied by a constant 150 m/s northward velocity, that
alone can contribute **66.75 m** to a conservative remainder. Yet the combined
elapsed time is essentially linear: its start-tag rounding defect is below
2.06 × 10⁻¹⁴ seconds, permitting a combined remainder below 4.12 × 10⁻¹⁴ seconds
for this interior query. This diagnoses an uncertainty-construction loss, not
an actual instrument timing error.

The next method will preserve the shared clock and combine force/gravity terms
before bounding them. Those changes require independent mathematical controls
and a separate native qualification; the completed results will stay unchanged.
Useful long-record bounds, global numerical treatment and observational-error
adequacy remain open, so new qualified aircraft prediction fits remain blocked.

[All six unions](README.md) · [Frozen allowance](PLAN.md) ·
[Shared-clock next plan](../ilvis0-clock-correlation/PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
