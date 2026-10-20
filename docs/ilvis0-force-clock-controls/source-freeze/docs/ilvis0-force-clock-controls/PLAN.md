# Common-clock force integration qualification

Qualify the exact integral and clocked-matrix components before native use.
Use six unchanged generated configurations and four cases each: a 16-packet
short clock domain, a 400-packet full clock domain, a 1,600-packet full clock
domain, and a 1,600-packet fixed clock. Short-domain sensitivity is a software
control, not a change to any aircraft calibration limit.

Each of 24 identities uses 12 predetermined/bounded parameter probes. Compare
the integral centres with an independent backward suffix-weight calculation.
Check the exact rational G/H remainder inequalities on all three axes at each
probe. Use an independent Rodrigues/reciprocal-gain matrix for the weighted
prediction. Retain all 27 physical derivative columns and the 51-column design.

Finite-step derivative checks use step 2e-6 and tolerance 3e-8 in the generated
output units. They are software checks, not a claim of a unique differential at
clipping boundaries. The declared clock linearization is protected by its exact
remainder. Matrix-weighted containment allows 3e-12 for the independent floating
oracle; it does not establish full floating-point interval certification.

Freeze 24 starts, 288 probes, 1,296 derivative evaluations, 1,728 exact G/H
inequalities, at most 336 independent history queries and 325,440 combined
packet visits. Cache a history only when its exact query time is identical;
26 physical directions leave the clock unchanged. Reserve before work.
Four workers use one numerical thread each; allow 180 cooperative seconds,
30 per integral calculation, zero native calls and zero native bounds. No
original aircraft reads, observed fits, retries, extensions or process signals.

Keep source/input/environment hashes and every failure. Component success does
not release native propagation, the typed prediction interface or aircraft fits.

[Clock derivation](../ilvis0-common-force-transform/CLOCK_PLAN.md) ·
[Native requirements](../ilvis0-common-force-transform/NATIVE_PLAN.md).
