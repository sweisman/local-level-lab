# Recorded acceleration-magnitude envelope assessment

## Scope and identities

Use the two previously selected development recordings: IMU8 stretch
`b365bdf39150ee6afc303ac1` and IMU21 stretch
`7df21c836bec5751f83c0cce`. Selection is inherited unchanged from the earlier
hardware-diversity comparison, not chosen for this diagnostic's output. This
is retrospective development evidence, not untouched confirmation.

On each stretch, use one-second windows centered at 10%, 50% and 90% of its
saved duration. Use all supported receiver epochs within 16 seconds of each
center for a degree-four local polynomial. Reject insufficient support,
receiver gaps over two seconds, longitude chart discontinuity or physical
domain failures. Keep every exclusion. Do not search for replacement windows.

Assess all three candidates under nominal 5 ms and packet-header integration
interval hypotheses. Both share the first saved interval origin. Allow one
common receiver/IMU offset in ±0.15 seconds. Keep only whole packets whose
possible support is inside the one-second window, and average every candidate
over exactly that retained interval union. No Group-1 attitude or gyro values
enter the scalar diagnostic.

## Declared uncertainty alternatives

Cross two receiver-coordinate boxes (1 m and 5 m horizontally and vertically)
with two acceleration-calibration boxes (gain ±1%, offset ±0.05 m/s²; gain
±15%, offset ±0.25 m/s²). These are sensitivity hypotheses, not verified
per-unit specifications or confidence intervals. The wider calibration box
matches earlier development limits; the narrower box tests an alternative
without claiming manufacturer support. Each axis has a shared constant
calibration interval; box propagation relaxes the dependence across packets.

Convert horizontal distance bounds to latitude/longitude bounds using
6,300,000 metres and the minimum cosine over receiver latitude plus its
latitude error. Reject unsupported polar bounds. This is an explicit coordinate
error convention under conventional receiver coordinates, not raw GNSS ranging.

The degree-four Taylor envelope declares absolute derivative bounds by order
for latitude/longitude/height, in radians/metres and seconds:

| Order | Latitude | Longitude | Height |
|---|---:|---:|---:|
| 0 | π/2 | 2π | 20,000 |
| 1 | 0.0001 | 0.0005 | 2 |
| 2 | 0.0000001 | 0.0000005 | 0.2 |
| 3 | 0.000000001 | 0.000000005 | 0.05 |
| 4 | 0.00000000001 | 0.00000000005 | 0.01 |
| 5 | 0.0000000000001 | 0.0000000000005 | 0.002 |

These explicit smoothness assumptions cover the Taylor remainder only when
they hold. They are not inferred from a low polynomial residual. Record
observable envelope conflicts, but absence of a conflict does not verify
unobserved high-frequency motion.

Use apparent gravity 9.70–9.90 m/s², one count per delta-velocity component,
the separately recorded IMU8/IMU21 conversion hypotheses, a corrected body-force
direction-rate bound of 1 rad/s and a continuous scalar magnitude-rate bound
of 2 m/s³. Periods are exact under each named integration hypothesis;
frequency error and time-varying latency are not implicitly covered. None of
these assumptions may be changed after viewing this assessment's outcomes.

Regression weighting is a fixed identity matrix, not an estimated covariance.
Coordinate measurement/truncation boxes propagate deterministically through
all nine trajectory quantities and the nonlinear candidate force calculation.
Do not shrink deterministic errors as independent noise. Estimate the force
box at every retained packet midpoint; include continuous averaging and common
offset bounds. Preserve physical and numerical failures separately.

## Finite allowance and outputs

- Two strict, hash-checked source extractions; no downloads or new selections.
- 24 receiver-operator batches: two recordings × three windows × two clocks ×
  two receiver-error boxes; at most 256 operators each, 6,144 total.
- 144 candidate identities: those 24 batches × two calibration boxes × three
  candidates; at most 256 force boxes each, 36,864 total.
- Zero optimizer starts, zero native trajectory integrations and no retries.
- One worker, four total numerical threads, 30-minute wall ceiling.

Charge each extraction, operator batch and candidate identity before work.
Interrupted identities remain charged. Source/input/environment hashes and
immutable artifacts must verify before continuing unfinished work. Completed
work never restarts. Preserve selected counts, timestamps, interval membership,
receiver inputs, parameter assumptions, outputs, exclusions and hashes.

Publish a compact table and CSV of measured/predicted envelopes and minimum
gaps for every identity, with unsupported intervals visible. Overlap is only
a non-exclusion by a necessary scalar constraint; it is not complete-history
feasibility. Disjoint boxes indicate incompatibility under the stated bounds,
not calibrated significance. Every scientific decision remains abstain.
Compare descriptively with the saved complete-observation findings, without
refits or relabeling earlier sensitivity failures.

[Combined controls](../ilvis0-measurement-contribution/COMBINED_BOUNDS.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
