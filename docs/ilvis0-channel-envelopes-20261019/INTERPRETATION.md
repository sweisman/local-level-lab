# What the acceleration-only assessment shows

**None of the three candidates is excluded by this scalar check.** All 144
candidate cases overlap under the frozen assumptions, with no unsupported cases.
The main complete-observation result remains **53 globe, zero flat**.

An **IMU (inertial measurement unit)** measures turning with gyroscopes and
specific force with accelerometers. This diagnostic omits the turning data and
compares only force magnitudes. It deliberately keeps the missing orientation
information missing; fused navigation is not inserted to supply it.

## Recordings and coverage

| Recording | IMU configuration | Complete stretch | Median speed | Mean latitude/course | Acceleration-only outcome |
|---|---|---:|---:|---|---|
| Ames 510, October 20 survey | IMU8 | 9.75 min | 849 km/h | 63.07°S / 203.7° | 72 overlapping cases |
| LVIS 610, April 9 survey | IMU21 | 4.07 min | 842 km/h | 71.89°N / 86.4° | 72 overlapping cases |

The full-position comparison favors globe on both complete stretches. The new
scalar assessment uses **three one-second snapshot windows per recording**, at
10%, 50% and 90% of the saved interval. Whole-packet support is reduced further
at uncertain time boundaries. This is a comparison on the same recordings,
**not a matched ablation over their entire observation histories**.

Every snapshot was evaluated under both integration clocks, both receiver-error
boxes, both calibration boxes and all three candidates. No replacement window,
new fit, gyro correction or changed original disposition was used. The
[recording CSV](matched-recordings.csv) preserves source hashes, UTC intervals,
geometry and the linked complete-observation dispositions.

## Why the envelopes overlap

The declared uncertainties are larger than the small scalar force differences
being investigated. For example, median measured envelopes under the narrower
calibration box span roughly **9.68–10.00 m/s²**. With the 1 m receiver-error
box, median prediction envelopes span approximately **9.03–10.58 m/s²** across
the two recordings. The wider coordinate/calibration alternatives expand them.
These are envelopes under assumptions, not measured sensor-noise levels.

The common ±0.15-second timing allowance alone contributes a ±0.30 m/s² bound
under the declared magnitude-rate envelope. Differentiation, truncation,
gravity and calibration add other contributions. These deterministic bounds
do not shrink as independent random errors.

Overlap means this necessary scalar constraint cannot exclude a candidate.
It does not demonstrate a complete feasible gyro-free reconstruction, identify
orientation, prove that one common calibration explains the full history, or
assign equal support to globe and flat. The gyro-based reconstruction still
strongly prefers globe; this intentionally reduced diagnostic does not reproduce
that discrimination.

## What remains

The next contribution comparison must cover the supported recording history,
keep shared calibration across its windows and report discarded edge/gap support.
It must distinguish a feasible scalar history from overlapping independent
envelopes. Physical error assumptions and correlated residual uncertainty remain
development questions; this assessment supplies no calibrated significance or
quantitative percentage of evidence attributable to gyroscopes.

Completed work used 3,336 receiver operators and 20,016 force boxes in 38.57 seconds,
with zero optimizer starts or native integrations. All 170 diagnostic identities
completed, all calculation counts are known, and 375 published artifacts verify.
The completed study cannot restart or donate its unused allowance.

[Results](README.md) · [Every case](envelopes.csv) · [Frozen plan](PLAN.md) ·
[Contribution overview](../ilvis0-measurement-contribution/README.md).
