# The common matrix component passes its qualification

All **24 generated controls pass**. Independent rotation and reciprocal-gain
calculations check 1,536 probes, 1,296 derivative evaluations and 6,144 weighted
matrix identities. All 27 physical derivative columns remain; the augmented
design retains 51 columns including the earlier and new shared errors.

This supplies the first component required by the propagation diagnosis: the
same calibration matrix can act on changing raw force samples at every epoch,
with its nonlinear error represented once. It does not yet integrate that
term or establish narrower complete prediction ranges.

The next derivation must preserve the exact midpoint update after factoring
out the matrix-weighted raw-force integrals. It must retain Coriolis, transport,
the common acceleration term, lever effects and coordinate metrics. A common
time offset changes those raw-force integrals, so its cross terms need explicit
bounds. The current component's fixed-vector identity does not cover them.

Native propagation, a typed 51-column training/prediction interface and the full
six-case/eight-sector comparison remain separate gates. No original aircraft
measurements, native integration calls or observed fits were used. The
53-stretch empirical findings and scientific abstention are unchanged.

[Qualification evidence](README.md) ·
[Mathematical plan](../ilvis0-common-force-transform/PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
